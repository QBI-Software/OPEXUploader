from os.path import join
import unittest2 as unittest
from opexuploader.dataparser.abstract.DataParser import DataParser
import sys
if sys.platform == 'win32':
    ROOTDATADIR = "Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata"
else:
    ROOTDATADIR = "/Volumes/project_humanexercise/DATA/DATA ENTRY/XnatUploaded/sampledata"

class TestCantabDataparser(unittest.TestCase):
    def setUp(self):
        try:
            datafile=join(ROOTDATADIR,'cantab','RowBySession_HealthyBrains_20180504.csv')
            sheet=0
            skip=0
            header=None
            etype='CANTAB'
            self.dp = None
            self.dp = DataParser(datafile, sheet, skip, header, etype)
        except Exception as e:
            print(e)


    def tearDown(self):
        if self.dp is not None:
            self.dp.dbi.closeconn()

    def test_info(self):
        if self.dp is not None:
            self.assertIsNone(self.dp.info)

    def test_fields(self):
        if self.dp is not None:
            self.assertEqual(len(self.dp.fields),0)

class TestDataparser(unittest.TestCase):
    def setUp(self):
        try:
            datafile=join(ROOTDATADIR,'blood','MULTIPLEX','2018-02-01 1058VB 1021LB 1107 1114.xlsx')
            sheet=0
            skip=1
            header=None
            etype='MULTIPLEX'
            self.dp = None
            self.dp = DataParser(datafile, sheet, skip, header, etype)
        except Exception as e:
            print(e)


    def tearDown(self):
        if self.dp is not None:
            self.dp.dbi.closeconn()

    def test_info(self):
        if self.dp is not None:
            expected = {'prefix': u'MPX', 'xsitype': u'opex:bloodMultiplexData'}
            self.assertDictEqual(expected,self.dp.info)

    def test_fields(self):
        if self.dp is not None:
            expected =[u'GH', u'Leptin', u'BDNF', u'IGFBP7', u'IL1', u'IL4', u'IL6', u'IL10']
            self.assertListEqual(expected, self.dp.fields)

    def test_prefix(self):
        if self.dp is not None and self.dp.info is not None:
            data = self.dp.getPrefix()
            expected = 'MPX'
            self.assertEqual(expected,data)

    def test_xsd(self):
        if self.dp is not None and self.dp.info is not None:
            data = self.dp.getxsd()
            expected = 'opex:bloodMultiplexData'
            self.assertEqual(expected,data)