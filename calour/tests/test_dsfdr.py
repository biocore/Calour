from unittest import TestCase, main

import numpy as np
import numpy.testing as npt

from calour import dsfdr

# cd dfdr
# source activate python3
# run nosetests in shell
# npt.almost equal (round to 1 if bigger than 0.5)


class FDRmethodsTests(TestCase):

    def setUp(self):
        np.random.seed(31)
        self.labels = np.array([1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
        self.data = np.array([[0, 1, 3, 5, 0, 1, 100, 300, 400, 500, 600, 700],
                              [1, 2, 3, 4, 5, 6, 6, 5, 4, 3, 2, 1],
                              [0, 0, 0, 0, 0, 1, 0, 0, 0, 3, 0, 1]])

        np.random.seed(31)
        self.data_sim, self.labels_sim = simulatedat(numsamples=10, numdiff=100, numc=100,
                                                     numd=800, sigma=0.1, normalize=False, numreads=10000)

    def test_dsfdr(self):
        # test on dummy self.data
        res_ds = dsfdr.dsfdr(self.data, self.labels, method='meandiff', transform='none',
                             alpha=0.1, numperm=1000, fdrmethod='dsfdr')
        self.assertEqual(np.shape(res_ds)[0], self.data.shape[0])
        np.testing.assert_array_equal(res_ds[0], [True, False, False])

        res_bh = dsfdr.dsfdr(self.data, self.labels, method='meandiff', transform='none',
                             alpha=0.1, numperm=1000, fdrmethod='bhfdr')
        self.assertEqual(np.shape(res_bh)[0], self.data.shape[0])
        np.testing.assert_array_equal(res_bh[0], [True, False, False])

        res_by = dsfdr.dsfdr(self.data, self.labels, method='meandiff', transform='none',
                             alpha=0.1, numperm=1000, fdrmethod='byfdr')
        self.assertEqual(np.shape(res_by)[0], self.data.shape[0])
        np.testing.assert_array_equal(res_by[0], [True, False, False])

        # test on simulated self.data_sim
        np.random.seed(31)
        res_ds2 = dsfdr.dsfdr(self.data_sim, self.labels_sim, method='meandiff', transform='none',
                              alpha=0.1, numperm=1000, fdrmethod='dsfdr')[0]
        fdr_ds2 = (np.sum(np.where(res_ds2)[0] >= 100)) / np.sum(res_ds2)
        np.testing.assert_equal(fdr_ds2 <= 0.1, True)

        np.random.seed(31)
        res_bh2 = dsfdr.dsfdr(self.data_sim, self.labels_sim, method='meandiff', transform='none',
                              alpha=0.1, numperm=1000, fdrmethod='bhfdr')[0]
        self.assertEqual(np.shape(res_bh2)[0], self.data_sim.shape[0])
        fdr_bh2 = (np.sum(np.where(res_bh2)[0] >= 100)) / np.sum(res_bh2)
        np.testing.assert_equal(fdr_bh2 <= 0.1, True)

        np.random.seed(31)
        res_by2 = dsfdr.dsfdr(self.data_sim, self.labels_sim, method='meandiff', transform='none',
                              alpha=0.1, numperm=1000, fdrmethod='byfdr')[0]
        self.assertEqual(np.shape(res_by2)[0], self.data_sim.shape[0])
        fdr_by2 = (np.sum(np.where(res_by2)[0] >= 100)) / np.sum(res_by2)
        np.testing.assert_equal(fdr_by2 <= 0.1, True)


def simulatedat(numsamples=5, numdiff=100, numc=100, numd=800, sigma=0.1, normalize=False, numreads=10000):
    """
    revised simulation code

    input:
    numsamples : int
            number of samples in each group
    numdiff : int
            number of different bacteria between the groups
    numc : int
            number of high freq. bacteria similar between the groups
    numd : int
            number of low freq. bacteria similar between the groups
    sigma : float
            the standard deviation
    """

    A = np.zeros([int(numdiff), 2 * numsamples])
    for i in range(int(numdiff)):
        mu_H = np.random.uniform(0.1, 1)
        mu_S = np.random.uniform(1.1, 2)
        h = np.random.normal(mu_H, sigma, numsamples)
        s = np.random.normal(mu_S, sigma, numsamples)
        # zero inflation
        h[h < 0] = 0
        s[s < 0] = 0
        # randomize the difference in S or H groups
        coin = np.random.randint(2)
        if coin == 0:
            A[i, :] = np.hstack((h, s))
        else:
            A[i, :] = np.hstack((s, h))

    C = np.zeros([numc, 2 * numsamples])
    for j in range(numc):
        mu = np.random.uniform(10, 11)
        C[j, :] = np.random.normal(mu, sigma, 2 * numsamples)

    numnoise = np.random.randint(1, 7, numd)
    D = np.zeros([numd, 2 * numsamples])
    for k in range(numd):
        for cnoise in range(numnoise[k]):
            cpos = np.random.randint(2 * numsamples)
            D[k, cpos] = np.random.uniform(0.1, 1)

    data = np.vstack((A, C, D))

    if normalize:
        data = data / np.sum(data, axis=0)  # normalize by column

    # labels
    x = np.array([0, 1])
    labels = np.repeat(x, numsamples)
    labels = (labels == 1)

    return (data, labels)


class StatisticsTests(TestCase):

    def setUp(self):
        self.labels = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        self.data = np.array([[0, 1, 3, 5, 10, 30, 40, 50],
                              [1, 2, 3, 4, 4, 3, 2, 1],
                              [0, 0, 0, 1, 0, 3, 0, 1]])

        self.labels2 = np.array([2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0, 0])
        self.data2 = np.array([[-1, 15, 2, 4, 0, 1, 3, 5, 10, 30, 40, 50],
                               [2, 1, 3, 4, 1, 2, 3, 4, 4, 3, 2, 1],
                               [1, 3, 3, 0, 0, 0, 0, 1, 0, 3, 0, 1]])

    def test_meandiff(self):
        res = dsfdr.meandiff(self.data, self.labels)
        self.assertEqual(len(res), self.data.shape[0])
        self.assertEqual(res[0], -30.25)
        self.assertEqual(res[1], 0)
        self.assertEqual(res[2], -0.75)

    def test_stdmeandiff(self):
        res = dsfdr.stdmeandiff(self.data, self.labels)
        self.assertEqual(len(res), self.data.shape[0])
        npt.assert_almost_equal(res[0], -1.57, decimal=2)
        self.assertEqual(res[1], 0)
        npt.assert_almost_equal(res[2], -0.39, decimal=2)

    def test_mannwhitney(self):
        res = dsfdr.mannwhitney(self.data, self.labels)
        self.assertEqual(len(res), self.data.shape[0])
        self.assertEqual(res[0], 0)
        self.assertEqual(res[1], 8)
        self.assertEqual(res[2], 5.5)

    def test_kruwallis(self):
        res = dsfdr.kruwallis(self.data2, self.labels2)
        self.assertEqual(len(res), self.data.shape[0])
        npt.assert_almost_equal(res[0], 6.58, decimal=2)
        self.assertEqual(res[1], 0)
        npt.assert_almost_equal(res[2], 2.55, decimal=2)

    def pearson(self):
        res = dsfdr.pearson(self.data, self.labels)
        self.assertEqual(len(res), self.data.shape[0])
        npt.assert_almost_equal(res[0], -0.82, decimal=2)
        self.assertEqual(res[1], 0)
        npt.assert_almost_equal(res[2], -0.38, decimal=2)

    def spearman(self):
        res = dsfdr.spearman(self.data, self.labels)
        self.assertEqual(len(res), self.data.shape[0])
        npt.assert_almost_equal(res[0], -0.87, decimal=2)
        self.assertEqual(res[1], 0)
        npt.assert_almost_equal(res[2], -0.31, decimal=2)


if __name__ == '__main__':
    main()
