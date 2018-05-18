from os.path import join, expanduser

import unittest2 as unittest

from opexuploader.uploader import OPEXUploader, create_parser

import sys
if sys.platform == 'win32':
    ROOTDATADIR = "Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata"
else:
    ROOTDATADIR = "/Volumes/project_humanexercise/DATA/DATA ENTRY/XnatUploaded/sampledata"


class TestUploader(unittest.TestCase):
    def setUp(self):
        parser = create_parser()
        args = parser.parse_args(['xnat-dev-opex', 'P1', '--projects', '--checks'])
        uploader = OPEXUploader(args)
        uploader.config()
        uploader.xnatconnect()
        self.uploader = uploader

    def tearDown(self):
        self.uploader.xnatdisconnect()

    def test_config(self):
        configfile = join(expanduser('~'), '.xnat.cfg')
        self.assertEqual(self.uploader.configfile, configfile)

    def test_xnatconnect(self):
        results = self.uploader.xnat.testconnection()
        self.assertEqual(results, True)

    def test_checks(self):
        self.assertEqual(self.uploader.args.checks, True)

    # def test_xnatdisconnect(self):
    #     self.uploader.xnatdisconnect()
    #     results = self.uploader.xnat.testconnection()
    #     self.assertEqual(results,False)

    def test_dataupload_CANTAB(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'cantab')
        runoption = 'cantab'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_ACER(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'acer')
        runoption = 'acer'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_AMUNET(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'amunet')
        runoption = 'amunet'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_MRIDATA(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'mridata')
        runoption = 'mridata'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_MULTIPLEX(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'blood', 'MULTIPLEX')
        runoption = 'blood'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_COBAS(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'blood', 'COBAS')
        runoption = 'blood'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_DEXA(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'dexa')
        runoption = 'dexa'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_DASS(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'dass')
        runoption = 'dass'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_GODIN(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'godin')
        runoption = 'godin'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_Insomnia(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'insomnia')
        runoption = 'insomnia'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_Psqi(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'psqi')
        runoption = 'psqi'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_Visit(self):
        project = 'P1'
        datadir = join(ROOTDATADIR, 'visit')
        runoption = 'visit'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUploader)
    unittest.TextTestRunner(verbosity=2).run(suite)