# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from unittest import main

import numpy as np
from numpy.testing import assert_array_almost_equal

import calour as ca
from calour._testing import Tests, assert_experiment_equal


class TestTransforming(Tests):
    def setUp(self):
        super().setUp()
        self.test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat)

    def test_transform(self):
        obs = self.test2.transform()
        self.assertEqual(obs, self.test2)
        self.assertIsNot(obs, self.test2)

        obs = self.test2.transform(inplace=True)
        self.assertIs(obs, self.test2)

    def test_scale(self):
        obs = self.test2.scale()
        self.assertIsNot(obs, self.test2)

        obs = self.test2.scale(inplace=True)
        self.assertIs(obs, self.test2)

    def test_log_n(self):
        obs = self.test2.log_n()
        self.test2.data = np.log2(
            [[10., 20., 1., 20., 5., 100., 844., 100.],
             [10., 20., 2., 19., 1., 100., 849., 200.],
             [10., 20., 3., 18., 5., 100., 844., 300.],
             [10., 20., 4., 17., 1., 100., 849., 400.],
             [10., 20., 5., 16., 4., 100., 845., 500.],
             [10., 20., 6., 15., 1., 100., 849., 600.],
             [10., 20., 7., 14., 3., 100., 846., 700.],
             [10., 20., 8., 13., 1., 100., 849., 800.],
             [10., 20., 9., 12., 7., 100., 842., 900.]])
        assert_experiment_equal(obs, self.test2)
        self.assertIsNot(obs, self.test2)

        obs = self.test2.log_n(inplace=True)
        self.assertIs(obs, self.test2)

    def test_normalize(self):
        total = 1000
        obs = self.test2.normalize(total)
        assert_array_almost_equal(obs.data.sum(axis=1).A1,
                                  [total] * 9)
        self.assertIsNot(obs, self.test2)

        obs = self.test2.normalize(total, inplace=True)
        self.assertIs(obs, self.test2)

    def test_normalize_filter_features(self):
        # test the filtering in standard mode (remove a few features, normalize to 10k)
        exp = ca.read(self.test1_biom, self.test1_samp)
        bad_features = [6, 7]
        features = [exp.feature_metadata.index[cbad] for cbad in bad_features]
        newexp = exp.normalize_filter_features(features, reads=10000, exclude=True, inplace=False)
        # see the mean of the features we want (without 6,7) is 10k
        good_features = list(set(range(exp.data.shape[1])).difference(set(bad_features)))
        assert_array_almost_equal(newexp.data[:, good_features].sum(axis=1), np.ones([exp.data.shape[0]])*10000)
        self.assertTrue(np.all(newexp.data[:, bad_features] > exp.data[:, bad_features]))


if __name__ == '__main__':
    main()
