from __future__ import print_function
import os
import unittest2 as unittest
from opexuploader.utils import findResourceDir

class TestCantabDataparser(unittest.TestCase):
    def setUp(self):
        pass

    def test_Tests(self):
        print('Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)

    def test_Root(self):
        os.chdir(os.path.dirname(os.getcwd()))
        print('Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)

    def test_Subdir(self):
        os.chdir(os.path.join(os.path.dirname(os.getcwd()),'opexuploader'))
        print('Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)

    def test_SubSubdir(self):
        os.chdir(os.path.join(os.path.dirname(os.getcwd()),'opexuploader','dataparser'))
        print('Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)

    def test_SubSubSubdir(self):
        os.chdir(os.path.join(os.path.dirname(os.getcwd()),'opexuploader','dataparser','abstract'))
        print('Current dir:', os.getcwd())
        resourcedir = findResourceDir()
        print('Resource dir: ', resourcedir)
        expected = 'resources'
        self.assertEqual(os.path.basename(resourcedir), expected)




