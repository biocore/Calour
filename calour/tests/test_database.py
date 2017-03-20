# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from unittest import main
from os.path import join
from tempfile import mkdtemp
import shutil

from calour._testing import Tests
from calour.tests.mock_database import MockDatabase
from calour.heatmap.heatmap import _create_plot_gui
import calour.util
from calour.database import _get_database_class
import calour as ca


class ExperimentTests(Tests):
    def setUp(self):
        super().setUp()
        self.mock_db = MockDatabase()
        self.test1 = ca.read_amplicon(self.test1_biom, self.test1_samp,
                                      filter_reads=1000, normalize=10000)
        self.s1 = 'TACGTATGTCACAAGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTAGGCCGTGGATTAAGCGTGTTGTGAAATGTAGACGCTCAACGTCTGAATCGCAGCGCGAACTGGTTCACTTGAGTATGCACAACGTAGGCGGAATTCGTCG'

    def test_mock_db(self):
        mdb = self.mock_db
        self.assertTrue(mdb.annotatable)
        self.assertTrue(mdb.can_get_feature_terms)
        self.assertEqual(mdb.database_name, 'mock_db')

    def test_gui_interface(self):
        mdb = self.mock_db
        res = mdb.get_seq_annotation_strings(self.s1)
        print(res)
        gui = _create_plot_gui(self.test1, gui='qt5', databases=[])
        gui.databases.append(mdb)
        res = gui.get_database_annotations(self.s1)
        print(res)

    def test_get_database_class(self):
        d = mkdtemp()
        f = join(d, 'config.txt')
        calour.util.set_config_value('class_name', 'MockDatabase', section='testdb', config_file_name=f)
        calour.util.set_config_value('module_name', 'calour.tests.mock_database', section='testdb', config_file_name=f)
        db = _get_database_class('testdb', config_file_name=f)
        self.assertEqual(db.database_name, 'mock_db')
        with self.assertRaises(ValueError):
            _get_database_class('mock')
        shutil.rmtree(d)


if __name__ == "__main__":
    main()
