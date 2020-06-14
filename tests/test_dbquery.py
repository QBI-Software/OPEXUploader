from os.path import join

import pandas
import unittest2 as unittest

from config.dbquery import DBI
from opexuploader.utils import findResourceDir


class TestDBquery(unittest.TestCase):
    def setUp(self):
        self.resourcedir = findResourceDir()
        configdb = join(self.resourcedir, 'opexconfig_test.db')
        self.dbi = DBI(configdb)
        self.dbi.getconn()

    def tearDown(self):
        self.dbi.conn.close()

    def test_getIDs(self):
        data = self.dbi.getIDs()
        self.assertGreater(len(data), 0)

    def test_updateIDs(self):
        df = pandas.read_csv(join('..', 'resources', 'incorrectIds.csv'))
        idlist = [(d['INCORRECT'], d['CORRECT']) for i, d in df.iterrows()]
        cnt = self.dbi.addIDs(idlist)
        expected = len(idlist)
        self.assertEqual(expected, cnt)

    def test_getRunOptions(self):
        data = self.dbi.getRunOptions()
        self.assertGreater(len(data), 0)

    def test_getFields(self):
        etype = 'CANTAB MOT'
        expected = [u'MOTML', u'MOTSDL', u'MOTTC', u'MOTTE']
        data = self.dbi.getFields(etype)
        print(etype, ": ", data)
        self.assertGreater(len(data), 0)
        self.assertListEqual(expected, data)

    def test_getInfo(self):
        etype = 'MULTIPLEX'
        expected = {'prefix': u'MPX', 'xsitype': u'opex:bloodMultiplexData'}
        data = self.dbi.getInfo(etype)
        print(etype, ": ", data)
        self.assertGreater(len(data), 0)
        self.assertDictEqual(expected, data)

    def test_getInfo_missing(self):
        etype = 'CANTAB'
        data = self.dbi.getInfo(etype)
        print(etype, ": ", data)
        self.assertIsNone(data)

    def test_getCorrectID(self):
        incorrectid = '1040DR'
        correctid = '1040DA'
        cid = self.dbi.getCorrectID(incorrectid)
        self.assertEqual(correctid, cid)

    def test_getCorrectID_missing(self):
        incorrectid = '1020HC'
        cid = self.dbi.getCorrectID(incorrectid)
        self.assertEqual(incorrectid, cid)

    def test_getDatelessExpts(self):
        data = self.dbi.getDatelessExpts()
        self.assertGreater(len(data), 0)

    def test_getExpts(self):
        data = self.dbi.getExpts()
        self.assertGreater(len(data), 0)

    def test_getXsitypeFromPrefix(self):
        prefix = 'MPX'
        expected = 'opex:bloodMultiplexData'
        data = self.dbi.getXsitypeFromPrefix(prefix)
        self.assertEqual(expected, data)

    def test_getTotal(self):
        expt = 'GODIN'
        expected = 5
        data = self.dbi.getTotal(expt)
        self.assertEqual(expected, data)

    def test_getInterval(self):
        expt = 'GODIN'
        expected = 3
        data = self.dbi.getInterval(expt)
        self.assertEqual(expected, data)

    def test_getInfo_TASK(self):
        """ Checking taskret and taskencode """
        expt = 'TASKRET'
        expected = 'opex:fmritaskret'
        data = self.dbi.getInfo(expt)
        self.assertEqual(expected, data['xsitype'])
        fields = self.dbi.getFields(expt)
        self.assertGreater(len(fields), 0)
        expt = 'TASKENCODE'
        expected = 'opex:fmritaskencode'
        data = self.dbi.getInfo(expt)
        self.assertEqual(expected, data['xsitype'])
        fields = self.dbi.getFields(expt)
        self.assertGreater(len(fields), 0)

