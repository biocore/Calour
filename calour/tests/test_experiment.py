# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from unittest import main

import numpy as np

from calour._testing import Tests, assert_experiment_equal
import calour as ca


class ExperimentTests(Tests):
    def setUp(self):
        super().setUp()
        self.test1 = ca.read(self.test1_biom, self.test1_samp)

    def test_reorder_samples(self):
        # keep only samples 5 and 4
        new = self.test1.reorder([5, 4], axis=0)

        self.assertEqual(new.data.shape[0], 2)
        self.assertEqual(new.data.shape[1], self.test1.data.shape[1])

        # test sample_metadata are correct
        self.assertEqual(new.sample_metadata['id'][0], 6)
        self.assertEqual(new.sample_metadata['id'][1], 5)

        # test data are correct
        sseq = ('TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCA'
                'GGCGGTTTTGTAAGTCTGATGTGAAATCCCCGGGCTCAACCTGGGAATTG'
                'CATTGGAGACTGCAAGGCTAGAATCTGGCAGAGGGGGGTAGAATTCCACG')
        seqpos = new.feature_metadata.index.get_loc(sseq)
        self.assertEqual(new.data[0, seqpos], 6)
        self.assertEqual(new.data[1, seqpos], 5)

    def test_reorder_inplace_features(self):
        # test inplace reordering of features
        sseq = ('TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCA'
                'GGCGGTTTTGTAAGTCTGATGTGAAATCCCCGGGCTCAACCTGGGAATTG'
                'CATTGGAGACTGCAAGGCTAGAATCTGGCAGAGGGGGGTAGAATTCCACG')
        self.test1.reorder([2, 0], axis=1, inplace=True)
        seqpos = self.test1.feature_metadata.index.get_loc(sseq)
        self.assertEqual(seqpos, 0)
        self.assertEqual(self.test1.data[0, seqpos], 1)
        self.assertEqual(self.test1.data[1, seqpos], 2)

    def test_reorder_round_trip(self):
        # test double permuting of a bigger data set
        exp = ca.read(self.timeseries_biom, self.timeseries_samp)

        rand_perm_samples = np.random.permutation(exp.data.shape[0])
        rand_perm_features = np.random.permutation(exp.data.shape[1])
        rev_perm_samples = np.argsort(rand_perm_samples)
        rev_perm_features = np.argsort(rand_perm_features)
        new = exp.reorder(rand_perm_features, axis=1, inplace=False)
        new.reorder(rand_perm_samples, axis=0, inplace=True)
        new.reorder(rev_perm_features, axis=1, inplace=True)
        new.reorder(rev_perm_samples, axis=0, inplace=True)

        assert_experiment_equal(new, exp)


if __name__ == "__main__":
    main()
