# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

import unittest

import calour as ca
from calour._testing import Tests, assert_experiment_equal


class TestTesting(Tests):
    def setUp(self):
        super().setUp()
        # load the test1 experiment as sparse
        self.test1 = ca.read(self.test1_biom, self.test1_samp)
        # load the timeseries experiment as sparse
        self.timeseries = ca.read(self.timeseries_biom, self.timeseries_samp)

    def test_assert_experiment_equal(self):
        # basic testing
        assert_experiment_equal(self.test1, self.test1)
        with self.assertRaises(AssertionError):
            assert_experiment_equal(self.test1, self.timeseries)

        # is copy working?
        newexp = self.test1.deepcopy()
        assert_experiment_equal(self.test1, newexp)

        # just data
        newexp = self.test1.deepcopy()
        newexp.data[2, 2] = 43
        with self.assertRaises(AssertionError):
            assert_experiment_equal(self.test1, newexp)

        # just sample metadata
        newexp = self.test1.deepcopy()
        newexp.sample_metadata['id', 0] = 42
        with self.assertRaises(AssertionError):
            assert_experiment_equal(self.test1, newexp)

        # just feature metadata
        newexp = self.test1.deepcopy()
        newexp.feature_metadata['taxonomy', 0] = '42'
        with self.assertRaises(AssertionError):
            assert_experiment_equal(self.test1, newexp)


if __name__ == "__main__":
    unittest.main()
