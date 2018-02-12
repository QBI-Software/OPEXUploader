import unittest2 as unittest
import argparse
from os.path import join, expanduser

from uploader import OPEXUploader, create_parser



class TestUploader(unittest.TestCase):
    def setUp(self):
        parser = create_parser()
        args =parser.parse_args(['xnat-dev-opex','P1','--projects','--checks'])
        uploader = OPEXUploader(args)
        uploader.config()
        uploader.xnatconnect()
        self.uploader = uploader

    def tearDown(self):
        self.uploader.xnatdisconnect()

    def test_config(self):
        configfile = join(expanduser('~'), '.xnat.cfg')
        self.assertEqual(self.uploader.configfile,configfile)

    def test_xnatconnect(self):
        results = self.uploader.xnat.testconnection()
        self.assertEqual(results,True)

    def test_checks(self):
        self.assertEqual(self.uploader.args.checks, True)

    # def test_xnatdisconnect(self):
    #     self.uploader.xnatdisconnect()
    #     results = self.uploader.xnat.testconnection()
    #     self.assertEqual(results,False)

    def test_dataupload_CANTAB(self):
        project = 'P1'
        datadir= '..\\sampledata\\cantab'
        runoption = 'cantab'
        (missing,matches) = self.uploader.runDataUpload(project,datadir,runoption)
        self.assertGreater(len(matches),0)

    def test_dataupload_ACER(self):
        project = 'P1'
        datadir= '..\\sampledata\\acer'
        runoption = 'acer'
        (missing,matches) = self.uploader.runDataUpload(project,datadir,runoption)
        self.assertGreater(len(matches),0)

    def test_dataupload_AMUNET(self):
        project = 'P1'
        datadir= '..\\sampledata\\amunet'
        runoption = 'amunet'
        (missing,matches) = self.uploader.runDataUpload(project,datadir,runoption)
        self.assertGreater(len(matches),0)

    def test_dataupload_MRIDATA(self):
        project = 'P1'
        datadir = '..\\sampledata\\mridata'
        runoption = 'mridata'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        self.assertGreater(len(matches), 0)

    def test_dataupload_MULTIPLEX(self):
        project = 'P1'
        datadir= '..\\sampledata\\blood\\MULTIPLEX'
        runoption = 'blood'
        (missing,matches) = self.uploader.runDataUpload(project,datadir,runoption)
        self.assertGreater(len(matches),0)

    def test_dataupload_COBAS(self):
        project = 'P1'
        datadir= '..\\sampledata\\blood\\COBAS'
        runoption = 'blood'
        (missing,matches) = self.uploader.runDataUpload(project,datadir,runoption)
        self.assertGreater(len(matches),0)

    def test_dataupload_DEXA(self):
        project = 'P1'
        datadir= '..\\sampledata\\dexa'
        runoption = 'dexa'
        (missing,matches) = self.uploader.runDataUpload(project,datadir,runoption)
        self.assertGreater(len(matches),0)


if __name__ == '__main__':
    unittest.main()