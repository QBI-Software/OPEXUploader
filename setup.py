'''
    QBI OPEX XNAT Uploader APP: setup.py (Windows 64bit MSI)
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
# Step 1. Build first
#   python setup.py build
#   View build dir contents and test exe
# Step 2. Create MSI distribution (Windows)
#   python setup.py bdist_msi
#   View dist dir contents
# then run bdist_msi
####
# Issues with pandas and python2.7
# pip install pypiwin32
# pandas/compat/__init__.py -> change import builtins to from future import builtins

# [Bad fix but only thing that works] NB To add Shortcut working dir - change cx_freeze/windist.py Line 61 : last None - > 'TARGETDIR'

import sys
from os import environ, getcwd
from os.path import join, dirname, normpath

from cx_Freeze import setup, Executable
from uploader import __version__

application_title = 'QBI OPEX XNAT Uploader'
main_python_file = 'uploader_app.py'

venvpython = join(sys.prefix,'Lib','site-packages')
mainpython = sys.real_prefix
#'D:\\Programs\\Python27\\python-2.7.10.amd64'

environ['TCL_LIBRARY'] = join(mainpython, 'tcl', 'tcl8.5')
environ['TK_LIBRARY'] = join(mainpython, 'tcl', 'tk8.5')
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

build_exe_options = {
    'includes': ['idna.idnadata','numpy.core._methods', 'numpy.lib.format','lxml._elementpath', 'distutils'],
    'excludes': ['PyQt4', 'PyQt5', 'scipy','notebook','matplotlib','mpl-data','sqlalchemy'],
    'packages': ['pandas',"pyxnat","appdirs",'xlrd','urllib','ast','math','lxml','pytz','six','numpy'],
    'include_files': [join(getcwd(),'gui','noname.py'), 'resources/',
                      join(mainpython, 'DLLs', 'tcl85.dll'),
                      join(mainpython, 'DLLs', 'tk85.dll')
     ],
    'include_msvcr': 1
}

setup(
    name=application_title,
    version=__version__ ,
    description='QBI OPEX XNAT Uploader',
    long_description=open('README.md').read(),
    author='Liz Cooper-Williams, QBI',
    author_email='e.cooperwilliams@uq.edu.au',
    maintainer='QBI Custom Software, UQ',
    maintainer_email='qbi-dev-admin@uq.edu.au',
    url='http://github.com/QBI-Software/OPEXUploader',
    license='GNU General Public License (GPL)',
    options={'build_exe': build_exe_options, },
    executables=[Executable(main_python_file, base=base, targetName='opexuploader.exe', icon='resources/upload_logo.ico',
                            shortcutName=application_title, shortcutDir='DesktopFolder')]
)
