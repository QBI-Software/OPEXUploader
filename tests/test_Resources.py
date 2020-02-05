from __future__ import print_function
import os
import unittest2 as unittest
from opexuploader.utils import findResourceDir

class TestResources(unittest.TestCase):
    def setUp(self):
        self.testdir = os.path.dirname(os.path.realpath(__file__))
        (self.rootdir, _) = os.path.split(self.testdir)
        print('Init Root dir: ', self.rootdir)

    def test_ResourceDir(self):
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)

    def test_Root(self):
        expected = 'OPEXUploader'
        self.assertEqual(os.path.basename(self.rootdir), expected)

    def test_UploaderDir(self):
        expected = os.path.join(self.rootdir,'opexuploader')
        print('Testing: ', expected)
        self.assertTrue(os.path.exists(expected))

    def test_DataparserDir(self):
        expected = os.path.join(self.rootdir, 'opexuploader','dataparser')
        print('Testing: ', expected)
        self.assertTrue(os.path.exists(expected))

    def test_FieldsDir(self):
        resourcedir = findResourceDir()
        expected = os.path.join(resourcedir, 'fields')
        print('Testing: ', expected)
        self.assertTrue(os.path.exists(expected))




