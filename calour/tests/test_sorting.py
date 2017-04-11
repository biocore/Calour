# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from unittest import main
from os.path import join

import pandas.util.testing as pdt

import calour as ca
from calour._testing import Tests, assert_experiment_equal


class SortingTests(Tests):
    def setUp(self):
        super().setUp()
        # load the simple experiment as sparse
        self.test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat, normalize=None)
        self.test1 = ca.read(self.test1_biom, self.test1_samp, normalize=None)
        # load the complex experiment as sparse
        self.timeseries = ca.read(self.timeseries_biom, self.timeseries_samp, normalize=None)

    def test_cluster_data(self):
        def log_and_scale(exp):
            exp.log_n(inplace=True)
            exp.scale(inplace=True, axis=1)
            return exp
        # no minimal filtering
        obs = self.test1.cluster_data(transform=log_and_scale)
        exp = ca.read(join(self.test_data_dir, 'test1.clustered.features.biom'),
                      self.test1_samp,
                      normalize=None)
        assert_experiment_equal(obs, exp, almost_equal=True)

    def test_sort_by_metadata_sample(self):
        # test sorting various fields (keeping the order)
        obs = self.timeseries.sort_by_metadata(
            field='MINUTES', inplace=True).sort_by_metadata(
                field='HOUR', inplace=True).sort_by_metadata(
                    field='DAY', inplace=True)
        self.assertIs(obs, self.timeseries)
        exp = ca.read(join(self.test_data_dir, 'timeseries.sorted.time.biom'),
                      join(self.test_data_dir, 'timeseries.sample'),
                      normalize=None)
        assert_experiment_equal(obs, exp, almost_equal=True)
        self.assertListEqual(obs.sample_metadata['MF_SAMPLE_NUMBER'].tolist(), list(range(1, 96)))

    def test_sort_samples(self):
        obs = self.timeseries.sort_samples('MINUTES', inplace=True).sort_samples(
                'HOUR', inplace=True).sort_samples(
                    'DAY', inplace=True)
        self.assertIs(obs, self.timeseries)
        exp = ca.read(join(self.test_data_dir, 'timeseries.sorted.time.biom'),
                      join(self.test_data_dir, 'timeseries.sample'),
                      normalize=None)
        assert_experiment_equal(obs, exp, almost_equal=True)
        self.assertListEqual(obs.sample_metadata['MF_SAMPLE_NUMBER'].tolist(), list(range(1, 96)))

    def test_sort_by_metadata_feature(self):
        obs = self.test2.sort_by_metadata(
            field='level2', axis=1).sort_by_metadata(
                field='level1', axis=1)
        self.assertIsNot(obs, self.test2)
        assert_experiment_equal(
            obs, self.test2.reorder(obs.feature_metadata['ori.order'], axis=1))
        self.assertListEqual(obs.feature_metadata['new.order'].tolist(), list(range(8)))

    def test_sort_by_data_sample(self):
        # sort sample based on the first and last features
        obs = self.test2.sort_by_data(subset=[0, 7])
        # the order is the same with original
        assert_experiment_equal(obs, self.test2)

        obs = self.test2.sort_by_data(subset=[0, 3])
        assert_experiment_equal(
            obs, self.test2.reorder(obs.sample_metadata['ori.order'], axis=0))
        self.assertListEqual(obs.sample_metadata['new.order'].tolist(), list(range(9)))

    def test_sort_by_data_feature(self):
        obs = self.timeseries.sort_by_data(axis=1)
        exp = ca.read(join(self.test_data_dir, 'timeseries.sorted.freq.biom'),
                      join(self.test_data_dir, 'timeseries.sample'),
                      normalize=None)
        assert_experiment_equal(obs, exp, almost_equal=True)

    def test_sort_centroid(self):
        exp = self.test1.sort_centroid()
        # we didn't change the samples
        pdt.assert_frame_equal(exp.sample_metadata, self.test1.sample_metadata)
        # we did change the features but only reordered
        self.assertEqual(set(exp.feature_metadata.index), set(self.test1.feature_metadata.index))
        # look if one feature is in the correct place
        self.assertEqual(exp.feature_metadata.index[1], self.test1.feature_metadata.index[4])

    def test_sort_abundance_mean(self):
        exp = self.test1.sort_abundance(key='mean')
        okseqs = ['TACGTAGGTCCCGAGCGTTGTCCGGATTTATTGGGCGTAAAGGGTGCGTA'
                  'GGCGGCCTGTTAAGTAAGTGGTTAAATTGTTGGGCTCAACCCAATCCGGC'
                  'CACTTAAACTGGCAGGCTAGAGTATTGGAGAGGCAAGTGGAATTCCATGT',
                  'TACGTATGTCACAAGCGTTATCCGGATTTATTGGGTGTAAAGGGTGCGTA'
                  'GACGGAAATGCAAGTTAGTTGTGAAATACCTCGGCTTAACTGAGGAACTG'
                  'CAACTAAAACTATATTTCTTGAGTATCGGAGGGGTTTGTGGAATTCCTAG',
                  'ACGT',
                  'TACGGAGGATGCGAGCGTTATCTGGAATCATTGGGTTTAAAGGGTCCGTA'
                  'GGCGGGTTGATAAGTCAGAGGTGAAAGCGCTTAGCTCAACTAAGCAACTG'
                  'CCTTTGAAACTGTCAGTCTTGAATGATTGTGAAGTAGTTGGAATGTGTAG',
                  'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCA'
                  'GGCGGTTATGTAAGACAGTTGTGAAATCCCCGGGCTCAACCTGGGAACTG'
                  'CATCTGTGACTGCATAGCTAGAGTACGGTAGAGGGGGATGGAATTCCGCG',
                  'TACGTATGTCACAAGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTA'
                  'GGCCGTGGATTAAGCGTGTTGTGAAATGTAGACGCTCAACGTCTGAATCG'
                  'CAGCGCGAACTGGTTCACTTGAGTATGCACAACGTAGGCGGAATTCGTCG',
                  'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCA'
                  'GGCGGTTTTGTAAGTCTGATGTGAAATCCCCGGGCTCAACCTGGGAATTG'
                  'CATTGGAGACTGCAAGGCTAGAATCTGGCAGAGGGGGGTAGAATTCCACG',
                  'TACGTAGGTGGCAAGCTTTGTCCTTCCTTATTTGGCGTAAAGCGCGCGCA'
                  'GGCGGCCTATCCAGTCTGTCTTAAAAGTTCGGGGCTCAACCCCGTGATGG'
                  'GATGGAAACTAGTAGGCTAGAGTATCGGAGAGGAAAGCGGAATTCCTAGT',
                  'TACATAGGTCGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGTTCGTA'
                  'GGCTGTTTATTAAGTCTGGAGTCAAATCCCAGGGCTCAACCCTGGCTCGC'
                  'TTTGGATACTGGTAAACTAGAGTTAGATAGAGGTAAGCAGAATTCCATGT',
                  'TACGTAGGGCGCGAGCGTTGTCCGGAATTATTGGGCGTAAAGGGCTTGTA'
                  'GGCGGTTGGTCGCGTCTGCCGTGAAATTCTCTGGCTTAACTGGAGGCGTG'
                  'CGGTGGGTACGGGCTGACTTGAGTGCGGTAGGGGAGACTGGAACTCCTGG',
                  'TACGTAGGGCGCGAGCGTTATCCGGAATTATTGGGCGTAAAGAGTGCGTA'
                  'GGTGGCATCTTAAGCGCAGGGTTTAAGGCAATGGCTCAACCATTGTTCGC'
                  'CTTGCGAACTGGGGTGCTTGAGTGCAGGAGGGGAAAGTGGAATTCCTAGT',
                  'AAAAAAAGGTCCAGGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTA'
                  'GGCGGACGATTAAGTCAGCTGCGAAAGTTTGCGGCTCAACCGTAAAATTG'
                  'CAGTTGAAACTGGTTGTCTTGAGTGCACGCAGGGATGTTGGAATTCATGG']
        self.assertEqual(list(exp.feature_metadata.index.values), okseqs)
        self.assertEqual(exp.shape, self.test1.shape)

    def test_sort_abundance_default(self):
        exp = self.test1.sort_abundance()
        okseqs = ['TACGTAGGTCCCGAGCGTTGTCCGGATTTATTGGGCGTAAAGGGTGCGTA'
                  'GGCGGCCTGTTAAGTAAGTGGTTAAATTGTTGGGCTCAACCCAATCCGGC'
                  'CACTTAAACTGGCAGGCTAGAGTATTGGAGAGGCAAGTGGAATTCCATGT',
                  'TACGTATGTCACAAGCGTTATCCGGATTTATTGGGTGTAAAGGGTGCGTA'
                  'GACGGAAATGCAAGTTAGTTGTGAAATACCTCGGCTTAACTGAGGAACTG'
                  'CAACTAAAACTATATTTCTTGAGTATCGGAGGGGTTTGTGGAATTCCTAG',
                  'ACGT',
                  'TACGGAGGATGCGAGCGTTATCTGGAATCATTGGGTTTAAAGGGTCCGTA'
                  'GGCGGGTTGATAAGTCAGAGGTGAAAGCGCTTAGCTCAACTAAGCAACTG'
                  'CCTTTGAAACTGTCAGTCTTGAATGATTGTGAAGTAGTTGGAATGTGTAG',
                  'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCA'
                  'GGCGGTTATGTAAGACAGTTGTGAAATCCCCGGGCTCAACCTGGGAACTG'
                  'CATCTGTGACTGCATAGCTAGAGTACGGTAGAGGGGGATGGAATTCCGCG',
                  'TACGTATGTCACAAGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTA'
                  'GGCCGTGGATTAAGCGTGTTGTGAAATGTAGACGCTCAACGTCTGAATCG'
                  'CAGCGCGAACTGGTTCACTTGAGTATGCACAACGTAGGCGGAATTCGTCG',
                  'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCA'
                  'GGCGGTTTTGTAAGTCTGATGTGAAATCCCCGGGCTCAACCTGGGAATTG'
                  'CATTGGAGACTGCAAGGCTAGAATCTGGCAGAGGGGGGTAGAATTCCACG',
                  'TACGTAGGTGGCAAGCTTTGTCCTTCCTTATTTGGCGTAAAGCGCGCGCA'
                  'GGCGGCCTATCCAGTCTGTCTTAAAAGTTCGGGGCTCAACCCCGTGATGG'
                  'GATGGAAACTAGTAGGCTAGAGTATCGGAGAGGAAAGCGGAATTCCTAGT',
                  'TACATAGGTCGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGTTCGTA'
                  'GGCTGTTTATTAAGTCTGGAGTCAAATCCCAGGGCTCAACCCTGGCTCGC'
                  'TTTGGATACTGGTAAACTAGAGTTAGATAGAGGTAAGCAGAATTCCATGT',
                  'TACGTAGGGCGCGAGCGTTGTCCGGAATTATTGGGCGTAAAGGGCTTGTA'
                  'GGCGGTTGGTCGCGTCTGCCGTGAAATTCTCTGGCTTAACTGGAGGCGTG'
                  'CGGTGGGTACGGGCTGACTTGAGTGCGGTAGGGGAGACTGGAACTCCTGG',
                  'AAAAAAAGGTCCAGGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTA'
                  'GGCGGACGATTAAGTCAGCTGCGAAAGTTTGCGGCTCAACCGTAAAATTG'
                  'CAGTTGAAACTGGTTGTCTTGAGTGCACGCAGGGATGTTGGAATTCATGG',
                  'TACGTAGGGCGCGAGCGTTATCCGGAATTATTGGGCGTAAAGAGTGCGTA'
                  'GGTGGCATCTTAAGCGCAGGGTTTAAGGCAATGGCTCAACCATTGTTCGC'
                  'CTTGCGAACTGGGGTGCTTGAGTGCAGGAGGGGAAAGTGGAATTCCTAGT']
        self.assertEqual(list(exp.feature_metadata.index.values), okseqs)
        self.assertEqual(exp.shape, self.test1.shape)

    def test_sort_abundance_subgroup(self):
        exp = self.test2.sort_abundance(subset={'#SampleID': ['S2']}, key='mean')
        okseqs = ['TACGGAGGATGCGAGCGTTATCTGGAATCATTGGGTTTAAAGGGTCCGTA'
                  'GGCGGGTTGATAAGTCAGAGGTGAAAGCGCTTAGCTCAACTAAGCAACTG'
                  'CCTTTGAAACTGTCAGTCTTGAATGATTGTGAAGTAGTTGGAATGTGTAG',
                  'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCA'
                  'GGCGGTTTTGTAAGTCTGATGTGAAATCCCCGGGCTCAACCTGGGAATTG'
                  'CATTGGAGACTGCAAGGCTAGAATCTGGCAGAGGGGGGTAGAATTCCACG',
                  'TACGTATGTCACAAGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTA'
                  'GGCCGTGGATTAAGCGTGTTGTGAAATGTAGACGCTCAACGTCTGAATCG'
                  'CAGCGCGAACTGGTTCACTTGAGTATGCACAACGTAGGCGGAATTCGTCG',
                  'TACGTAGGTGGCAAGCTTTGTCCTTCCTTATTTGGCGTAAAGCGCGCGCA'
                  'GGCGGCCTATCCAGTCTGTCTTAAAAGTTCGGGGCTCAACCCCGTGATGG'
                  'GATGGAAACTAGTAGGCTAGAGTATCGGAGAGGAAAGCGGAATTCCTAGT',
                  'TACATAGGTCGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGTTCGTA'
                  'GGCTGTTTATTAAGTCTGGAGTCAAATCCCAGGGCTCAACCCTGGCTCGC'
                  'TTTGGATACTGGTAAACTAGAGTTAGATAGAGGTAAGCAGAATTCCATGT',
                  'TACGTAGGGCGCGAGCGTTGTCCGGAATTATTGGGCGTAAAGGGCTTGTA'
                  'GGCGGTTGGTCGCGTCTGCCGTGAAATTCTCTGGCTTAACTGGAGGCGTG'
                  'CGGTGGGTACGGGCTGACTTGAGTGCGGTAGGGGAGACTGGAACTCCTGG',
                  'AAAAAAAGGTCCAGGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTA'
                  'GGCGGACGATTAAGTCAGCTGCGAAAGTTTGCGGCTCAACCGTAAAATTG'
                  'CAGTTGAAACTGGTTGTCTTGAGTGCACGCAGGGATGTTGGAATTCATGG',
                  'TACGTAGGGCGCGAGCGTTATCCGGAATTATTGGGCGTAAAGAGTGCGTA'
                  'GGTGGCATCTTAAGCGCAGGGTTTAAGGCAATGGCTCAACCATTGTTCGC'
                  'CTTGCGAACTGGGGTGCTTGAGTGCAGGAGGGGAAAGTGGAATTCCTAGT']
        self.assertEqual(exp.feature_metadata.index.tolist(), okseqs)
        self.assertEqual(exp.shape, self.test2.shape)

    def test_cluster_features(self):
        exp = self.test1.cluster_features()
        okseqs = ['TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCA'
                  'GGCGGTTATGTAAGACAGTTGTGAAATCCCCGGGCTCAACCTGGGAACTG'
                  'CATCTGTGACTGCATAGCTAGAGTACGGTAGAGGGGGATGGAATTCCGCG',
                  'TACATAGGTCGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGTTCGTA'
                  'GGCTGTTTATTAAGTCTGGAGTCAAATCCCAGGGCTCAACCCTGGCTCGC'
                  'TTTGGATACTGGTAAACTAGAGTTAGATAGAGGTAAGCAGAATTCCATGT',
                  'TACGTATGTCACAAGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTA'
                  'GGCCGTGGATTAAGCGTGTTGTGAAATGTAGACGCTCAACGTCTGAATCG'
                  'CAGCGCGAACTGGTTCACTTGAGTATGCACAACGTAGGCGGAATTCGTCG',
                  'TACGTAGGTGGCAAGCTTTGTCCTTCCTTATTTGGCGTAAAGCGCGCGCA'
                  'GGCGGCCTATCCAGTCTGTCTTAAAAGTTCGGGGCTCAACCCCGTGATGG'
                  'GATGGAAACTAGTAGGCTAGAGTATCGGAGAGGAAAGCGGAATTCCTAGT',
                  'TACGTAGGGCGCGAGCGTTGTCCGGAATTATTGGGCGTAAAGGGCTTGTA'
                  'GGCGGTTGGTCGCGTCTGCCGTGAAATTCTCTGGCTTAACTGGAGGCGTG'
                  'CGGTGGGTACGGGCTGACTTGAGTGCGGTAGGGGAGACTGGAACTCCTGG',
                  'TACGTAGGGCGCGAGCGTTATCCGGAATTATTGGGCGTAAAGAGTGCGTA'
                  'GGTGGCATCTTAAGCGCAGGGTTTAAGGCAATGGCTCAACCATTGTTCGC'
                  'CTTGCGAACTGGGGTGCTTGAGTGCAGGAGGGGAAAGTGGAATTCCTAGT',
                  'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCA'
                  'GGCGGTTTTGTAAGTCTGATGTGAAATCCCCGGGCTCAACCTGGGAATTG'
                  'CATTGGAGACTGCAAGGCTAGAATCTGGCAGAGGGGGGTAGAATTCCACG',
                  'AAAAAAAGGTCCAGGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTA'
                  'GGCGGACGATTAAGTCAGCTGCGAAAGTTTGCGGCTCAACCGTAAAATTG'
                  'CAGTTGAAACTGGTTGTCTTGAGTGCACGCAGGGATGTTGGAATTCATGG',
                  'TACGGAGGATGCGAGCGTTATCTGGAATCATTGGGTTTAAAGGGTCCGTA'
                  'GGCGGGTTGATAAGTCAGAGGTGAAAGCGCTTAGCTCAACTAAGCAACTG'
                  'CCTTTGAAACTGTCAGTCTTGAATGATTGTGAAGTAGTTGGAATGTGTAG',
                  'TACGTATGTCACAAGCGTTATCCGGATTTATTGGGTGTAAAGGGTGCGTA'
                  'GACGGAAATGCAAGTTAGTTGTGAAATACCTCGGCTTAACTGAGGAACTG'
                  'CAACTAAAACTATATTTCTTGAGTATCGGAGGGGTTTGTGGAATTCCTAG',
                  'TACGTAGGTCCCGAGCGTTGTCCGGATTTATTGGGCGTAAAGGGTGCGTA'
                  'GGCGGCCTGTTAAGTAAGTGGTTAAATTGTTGGGCTCAACCCAATCCGGC'
                  'CACTTAAACTGGCAGGCTAGAGTATTGGAGAGGCAAGTGGAATTCCATGT',
                  'ACGT']
        self.assertListEqual(list(exp.feature_metadata.index.values), okseqs)


if __name__ == "__main__":
    main()
