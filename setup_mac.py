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


from os.path import join, dirname
from setuptools import setup
from os import getcwd
from uploader_app import __version__

application_title = 'QBI OPEX XNAT Uploader'
exe_name='opex_uploader'

plist = dict(CFBundleDisplayName=application_title,
	         CFBundleName=exe_name,
             NSHumanReadableCopyright='Copyright (2018) Queensland Brain Institute, University of Queensland',
             CFBundleTypeIconFile='upload_logo.icns',
             CFBundleVersion=__version__)

APP = ['uploader_app.py']
DATA_FILES = ['gui', 'resources']
PARENTDIR= join(getcwd(),'.')
OPTIONS = {'argv_emulation': True, 'plist':plist,
           'iconfile': join('resources','upload_logo.icns'),
           'includes': ['idna.idnadata','numpy.core._methods', 'numpy.lib.format','lxml._elementpath'],
           'excludes': ['PyQt4', 'PyQt5', 'scipy','notebook','matplotlib','mpl-data','sqlalchemy'],
           'packages': ['pandas','pyxnat','xlrd','urllib','ast','math','lxml','pytz','six','numpy']
           }

setup(app=APP, data_files=DATA_FILES,options={'py2app':OPTIONS},
      setup_requires=['py2app', 'pyobjc-framework-Cocoa', 'numpy', 'scipy'],)

# Add info to MacOSX plist
# plist = Plist.fromFile('Info.plist')
plist = dict(CFBundleDisplayName=application_title,
	         CFBundleName=exe_name,
             NSHumanReadableCopyright='Copyright (c) 2018 Queensland Brain Institute',
             CFBundleTypeIconFile='measure.ico.icns',
             CFBundleVersion=__version__
             )

APP = ['runapp.py']
DATA_FILES = ['resources', 'gui']
PARENTDIR= join(getcwd(),'.')
OPTIONS = {'argv_emulation': True,
           'plist': plist,
           'iconfile': 'resources/measure.ico.icns',
           'packages': ['scipy', 'wx','pandas','msdapp'],
           'includes':['six','appdirs','packaging','packaging.version','packaging.specifiers','packaging.requirements','os','numbers','future_builtins'],
           'bdist_base': join(PARENTDIR, 'build'),
           'dist_dir': join(PARENTDIR, 'dist'),
           }

setup( name=exe_name,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app','pyobjc-framework-Cocoa','numpy','scipy'],
)
