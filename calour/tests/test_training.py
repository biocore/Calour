# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from unittest import main
from os.path import join

from numpy.testing import assert_array_equal
import numpy as np
import pandas as pd
import pandas.util.testing as pdt
from sklearn import datasets
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.model_selection import KFold

import calour as ca
from calour._testing import Tests
from calour.training import plot_cm, plot_roc, plot_scatter, SortedStratifiedKFold, RepeatedSortedStratifiedKFold


class TTests(Tests):
    def setUp(self):
        super().setUp()
        self.test2_sparse = ca.read(self.test2_biom, self.test2_samp, self.test2_feat, normalize=None)
        self.test2_dense = ca.read(self.test2_biom, self.test2_samp, self.test2_feat, sparse=False, normalize=None)

    def test_add_sample_metadata_as_features(self):
        new = self.test2_sparse.add_sample_metadata_as_features(['categorical'])
        dat = new.data.toarray()
        assert_array_equal(dat[:, 0:3],
                           [[1, 0, 0], [0, 1, 0], [0, 0, 1]] * 3)
        self.assertListEqual(new.feature_metadata.index[:3].tolist(),
                             ['categorical=A', 'categorical=B', 'categorical=C'])

    def test_add_sample_metadata_as_features_dense(self):
        new = self.test2_dense.add_sample_metadata_as_features(['categorical'])
        assert_array_equal(new.data[:, 0:3],
                           [[1, 0, 0], [0, 1, 0], [0, 0, 1]] * 3)
        self.assertListEqual(new.feature_metadata.index[:3].tolist(),
                             ['categorical=A', 'categorical=B', 'categorical=C'])

    def test_split_train_test(self):
        train_X, test_X, train_y, test_y = self.test2_dense.split_train_test(
            test_size=3, field='group', stratify='categorical', random_state=7)
        self.assertListEqual(test_y.tolist(), [1, 2, 1])
        self.assertListEqual(test_y.index.tolist(), ['S3', 'S8', 'S1'])
        self.assertListEqual(train_y.tolist(), [2, 1, 1, 1, 1, 1])
        self.assertListEqual(train_y.index.tolist(), ['S9', 'S6', 'S5', 'S2', 'S4', 'S7'])

    def test_regress(self):
        diabetes = datasets.load_diabetes()
        X = diabetes.data[:9]
        y = diabetes.target[:9]
        smd = pd.DataFrame({'diabetes': y})
        exp = ca.Experiment(X, smd, sparse=False)
        run = exp.regress('diabetes', KNeighborsRegressor(), KFold(3, random_state=0))
        res = next(run)
        obs = pd.read_table(join(self.test_data_dir, 'diabetes_pred.txt'), index_col=0)
        pdt.assert_frame_equal(res, obs)

    def test_plot_scatter(self):
        res = pd.read_table(join(self.test_data_dir, 'diabetes_pred.txt'), index_col=0)
        title = 'foo'
        ax = plot_scatter(res, title=title)
        self.assertEqual(title, ax.get_title())
        cor = 'r=-0.62 p-value=0.078'
        self.assertEqual(cor, ax.texts[0].get_text())
        dots = []
        for collection in ax.collections:
            dots.append(collection.get_offsets())
        assert_array_equal(np.concatenate(dots, axis=0),
                           res[['Y_TRUE', 'Y_PRED']].values)

    def test_classify(self):
        iris = datasets.load_iris()
        n = len(iris.target)
        np.random.seed(0)
        i = np.random.randint(0, n, 36)
        X = iris.data[i]
        y = iris.target[i]
        d = dict(enumerate(iris.target_names))
        smd = pd.DataFrame({'plant': y}).replace(d)
        exp = ca.Experiment(X, smd, sparse=False)
        run = exp.classify('plant', KNeighborsClassifier(),
                           predict='predict_proba',
                           cv=KFold(3, random_state=0))
        res = next(run)
        obs = pd.read_table(join(self.test_data_dir, 'iris_pred.txt'), index_col=0)
        pdt.assert_frame_equal(res, obs)
        # plot_roc(res)
        # from matplotlib import pyplot as plt
        # plt.show()

    def test_plot_roc_multi(self):
        result = pd.read_table(join(self.test_data_dir, 'iris_pred.txt'))
        ax = plot_roc(result)
        legend = ax.get_legend()
        exp = {'Luck',
               'setosa (0.99 $\pm$ 0.00)',
               'virginica (0.96 $\\pm$ 0.05)',
               'versicolor (0.95 $\\pm$ 0.07)'}
        obs = {i.get_text() for i in legend.get_texts()}
        self.assertSetEqual(exp, obs)
        # from matplotlib import pyplot as plt
        # plt.show()

    def test_plot_roc_binary(self):
        result = pd.read_table(join(self.test_data_dir, 'iris_pred.txt'))
        result['Y_TRUE'] = ['virginica' if i == 'virginica' else 'not virginica'
                            for i in result['Y_TRUE']]
        result['not virginica'] = 1 - result['virginica']
        ax = plot_roc(result, pos_label='virginica')
        # from matplotlib import pyplot as plt
        # plt.show()
        legend = ax.get_legend()
        exp = {'Luck',
               'virginica (0.96 $\pm$ 0.05)'}
        obs = {i.get_text() for i in legend.get_texts()}
        self.assertSetEqual(exp, obs)

    def test_plot_cm(self):
        result = pd.read_table(join(self.test_data_dir, 'iris_pred.txt'), index_col=0)
        ax = plot_cm(result, labels=['setosa', 'virginica', 'versicolor'])
        # from matplotlib import pyplot as plt
        # plt.show()

        # make sure you don't confuse x, y label
        self.assertEqual(ax.get_xlabel(), 'Prediction')
        self.assertEqual(ax.get_ylabel(), 'Observation')

        obs = [((0, 0), '13'), ((1, 0), '0'), ((2, 0), '0'),
               ((0, 1), '0'), ((1, 1), '9'), ((2, 1), '1'),
               ((0, 2), '0'), ((1, 2), '3'), ((2, 2), '10')]
        for exp, obs in zip(ax.texts, obs):
            self.assertEqual(exp.get_text(), obs[1])
            self.assertEqual(exp.get_position(), obs[0])


class RTests(Tests):
    def setUp(self):
        self.y = np.array([9.1, 7.1, 8.1, 5.1, 3.1, 1.1, 2.1, 6.1, 4.1])
        self.X = self.y[:, np.newaxis]

    def test_sorted_stratified_k3(self):
        k = SortedStratifiedKFold(3, shuffle=True, random_state=9)
        splits = [[9.1, 8.1, 5.1, 3.1, 2.1, 4.1], [7.1, 1.1, 6.1],
                  [7.1, 8.1, 1.1, 2.1, 6.1, 4.1], [9.1, 5.1, 3.1],
                  [9.1, 7.1, 5.1, 3.1, 1.1, 6.1], [8.1, 2.1, 4.1]]

        for i, (train, test) in enumerate(k.split(self.X, self.y)):
            exp_train = splits[i * 2]
            exp_test = splits[i * 2 + 1]
            assert_array_equal(self.y[train], exp_train)
            assert_array_equal(self.y[test], exp_test)
            assert_array_equal(self.X[train], np.array(exp_train)[:, np.newaxis])
            assert_array_equal(self.X[test], np.array(exp_test)[:, np.newaxis])

    def test_sorted_stratified_k2(self):
        # another split scheme
        k = SortedStratifiedKFold(2, shuffle=True, random_state=9)
        split1, split2 = [9.1, 7.1, 5.1, 3.1, 1.1], [8.1, 2.1, 6.1, 4.1]

        for (train, test), exp in zip(k.split(self.X, self.y), [(split1, split2), (split2, split1)]):
            assert_array_equal(self.y[train], exp[0])
            assert_array_equal(self.y[test], exp[1])
            assert_array_equal(self.X[train], np.array(exp[0])[:, np.newaxis])
            assert_array_equal(self.X[test], np.array(exp[1])[:, np.newaxis])

    def test_rep_sorted_strtified_k2(self):
        k = RepeatedSortedStratifiedKFold(2, 3, random_state=9)
        splits = [[9.1, 8.1, 5.1, 3.1, 1.1], [7.1, 2.1, 6.1, 4.1],
                  [7.1, 2.1, 6.1, 4.1], [9.1, 8.1, 5.1, 3.1, 1.1],
                  [8.1, 5.1, 1.1, 4.1], [9.1, 7.1, 3.1, 2.1, 6.1],
                  [9.1, 7.1, 3.1, 2.1, 6.1], [8.1, 5.1, 1.1, 4.1],
                  [9.1, 7.1, 3.1, 1.1, 6.1], [8.1, 5.1, 2.1, 4.1],
                  [8.1, 5.1, 2.1, 4.1], [9.1, 7.1, 3.1, 1.1, 6.1]]

        for i, (train, test) in enumerate(k.split(self.X, self.y)):
            exp_train = splits[i * 2]
            exp_test = splits[i * 2 + 1]
            assert_array_equal(self.y[train], exp_train)
            assert_array_equal(self.y[test], exp_test)
            assert_array_equal(self.X[train], np.array(exp_train)[:, np.newaxis])
            assert_array_equal(self.X[test], np.array(exp_test)[:, np.newaxis])


if __name__ == "__main__":
    main()
