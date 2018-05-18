'''
    QBI OPEX XNAT Uploader APP: setup.py (MAC OSX)
    *******************************************************************************
    Copyright (C) 2017  QBI Software, The University of Queensland

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
'''
#
#   python setup.py py2app
#
# Usage:
#     python setup_mac.py py2app --matplotlib-backends='-'
#
# can test with -A first - then full zipped version
# > ./dist/opexuploader.app/Contents/MacOS/opexuploader
#
# Notes:
#     Clean on reruns:
#     > rm -rf build dist __pycache__
#     May need to use system python rather than virtualenv
#     > /Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7 setup_mac.py py2app --matplotlib-backends='-' > build.log
#  Specify matplotlib backends with '-'
#     Macholib version=1.7 required to prevent endless recursions - also need to downgrade py2app==0.10 and fix MachO header error: bug in MachOGraph line 49:
#  change loader=loader.filename TO loader_path=loader.filename
#

from os import getcwd
from os.path import join

from setuptools import setup

from opexuploader.uploader import __version__

application_title = 'QBI OPEX XNAT Uploader'
exe_name = 'opexuploader'
main_python_file = 'uploader_app.py'

plist = dict(CFBundleDisplayName=application_title,
             CFBundleName=exe_name,
             NSHumanReadableCopyright='Copyright (2018) Queensland Brain Institute, University of Queensland',
             CFBundleTypeIconFile='upload_logo.icns',
             CFBundleVersion=__version__)

APP = [main_python_file]
DATA_FILES = [join('opexuploader', 'gui'), 'resources/', 'README.md',]
PARENTDIR = join(getcwd(), '.')
OPTIONS = {'argv_emulation': True, 'plist': plist,
           'iconfile': join('resources', 'upload_logo.icns'),
           'packages': ['sqlite3', 'wx', 'pandas','openpyxl','pyxnat','certifi','xlrd','urllib','ast','math','lxml','pytz'],
           'includes': ['six', 'appdirs', 'os', 'numbers', 'future_builtins',
                        'packaging', 'packaging.version', 'packaging.specifiers', 'packaging.requirements', ],
           'bdist_base': join(PARENTDIR, 'build'),
           'dist_dir': join(PARENTDIR, 'dist'),

           }

setup(name=exe_name,
      app=APP,
      data_files=DATA_FILES,
      options={'py2app': OPTIONS},
      setup_requires=['py2app', 'pyobjc-framework-Cocoa', 'numpy'],
      )
