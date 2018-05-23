from __future__ import print_function
import os
import unittest2 as unittest
from opexuploader.utils import findResourceDir

class TestResources(unittest.TestCase):
    def setUp(self):
        self.rootdir = 'D:\\Projects\\OPEXUploader'
        print('Init Root dir: ', self.rootdir)

    def test_Tests(self):
        os.chdir(os.path.join(self.rootdir, 'tests'))
        print('Tests Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)

    def test_Root(self):
        os.chdir(self.rootdir)
        print('Root Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)

    def test_Subdir(self):
        os.chdir(os.path.join(self.rootdir,'opexuploader'))
        print('Subdir: Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)

    def test_SubSubdir(self):
        os.chdir(os.path.join(self.rootdir,'opexuploader','dataparser'))
        print('Subsubdir: Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)

    def test_SubSubSubdir(self):
        os.chdir(os.path.join(self.rootdir,'opexuploader','dataparser','abstract'))
        print('SubSubSubdir: Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)




