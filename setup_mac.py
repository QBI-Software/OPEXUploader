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


__version__='1.0.0'

from os.path import join, dirname
from setuptools import setup


plist = dict(CFBundleDisplayName='QBI OPEX XNAT Uploader',
             NSHumanReadableCopyright='Copyright (2017) Queensland Brain Institute, University of Queensland',
             CFBundleTypeIconFile=join('resources', 'upload_logo.ico'),
             CFBundleVersion=__version__)

APP = ['uploader_app.py']
DATA_FILES = [join(dirname(__file__),'gui','noname.py'), 'resources']
OPTIONS = {'argv_emulation': True, 'plist':plist,
           'iconfile': join('resources', 'upload_logo.ico'),
           'includes': ['idna.idnadata','numpy.core._methods', 'numpy.lib.format','lxml._elementpath'],
           'excludes': ['PyQt4', 'PyQt5', 'scipy','notebook','matplotlib','mpl-data','sqlalchemy'],
           'packages': ['pandas','pyxnat','xlrd','urllib','ast','math','lxml','pytz','six','numpy']
           }

setup(app=APP, data_files=DATA_FILES,options={'py2app':OPTIONS}, setup_requires=['py2app'])
