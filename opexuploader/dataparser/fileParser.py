"""
Title:  File Checker
Author: Alan Ho
Date:   30/01/2019

1. Generate a bunch of files within directories for other things like dexa, fitbit etc
2. Do something about the subject, interval parsing

"""
import re
import pandas as pd
import numpy as np
import os
from os.path import join, basename, getmtime, getctime, dirname, expanduser
import xlsxwriter
import random
import string
import random
import itertools
import time
import argparse
import sys

sys.path.append(os.getcwd())
from xnatconnect.XnatConnector import XnatConnector
from XnatQuery import XnatQuery


class FileParser:
    
    def __init__(self, inputdir):
        self.inputdir = inputdir
        self.filepattern = ''
        self.subjectpattern = "^[:0-9:]{4}[:A-Z:]{2}(?=_)"
        self.intervalpattern = '(?<=_)\d*(?=Month|Mon|M)'


    def getFiles(self):
        "You need to use absolute paths e.g. with os.path.walk"
        files = [os.path.join(d, x)
                    for d, dirs, files in os.walk(self.inputdir)
                    for x in files if bool(re.match(self.filepattern, basename(x)))]

        self.numberoffiles = len(self.files)
        print('Finished getting files')

    def parseFiles(self):
        "Now you need to be able to parse different types of file patterns"

        files_info = {'Subject': [], 'interval': [] ,'FILE': [], 'DATE_CREATED': [], 'LAST_MODIFIED': [], 'PARENT_DIR': []}
        for f in self.files:
            print(('PROCESSING: ' + basename(f)))
            subject = re.findall(self.subjectpattern, basename(f))[0]
            interval = re.findall(self.intervalpattern, basename(f))[0]
            date_created = time.ctime(getctime(f))
            date_modified = time.ctime(getmtime(f))
            files_info['Subject'].append(subject)
            files_info['interval'].append(int(interval))
            files_info['FILE'].append(basename(f))
            files_info['DATE_CREATED'].append(date_created)
            files_info['LAST_MODIFIED'].append(date_modified)
            files_info['PARENT_DIR'].append(dirname(f))
            self.files_info = pd.DataFrame.from_dict(files_info).\
                                sort_values(['Subject', 'interval']). \
                                assign(ID=lambda x: x['Subject'].str.slice(0, 4))


class AccelFiles:

    def __init__(self, inputdir):
        self.inputdir = inputdir
        self.filepattern = '^.*30sec.agd$'
        self.subjectpattern = '^[:0-9:]{4}[:A-Z:]{2}'
        self.intervalpattern = '^'

        self.getFiles()
        self.parseFiles()

    def getFiles(self):

        self.files = [f for f in os.listdir(self.inputdir) if bool(re.match(self.filepattern, f))]


    def parseFiles(self):

        files_info = {'Subject': [], 'interval': [], 'FILE': [], 'PARENT_DIR': []}
        for f in self.files:
            print(('PROCESSING: ' + basename(f)))
            splitfile = re.split('_', f)
            subject = splitfile[0]

            interval = re.findall('.*(?=M|m)|BL', splitfile[1])[0]
            interval = '0' if interval == 'BL' else interval

            print((subject, interval))
            # date_created = time.ctime(getctime(f))
            # date_modified = time.ctime(getmtime(f))

            files_info['Subject'].append(subject)
            files_info['interval'].append(int(interval))
            files_info['FILE'].append(basename(f))
            # files_info['DATE_CREATED'].append(date_created)
            # files_info['LAST_MODIFIED'].append(date_modified)
            files_info['PARENT_DIR'].append(dirname(f))
            self.files_info = pd.DataFrame.from_dict(files_info).\
                                sort_values(['Subject', 'interval']). \
                                assign(ID=lambda x: x['Subject'].str.slice(0, 4))


class XlsxFiles:

    def __init__(self, inputdir, IDcol = 'Participant ID', intervalcol='Time Point'):
        self.inputdir = inputdir

        self.getData()

    def getData(self):

        self.files = os.listdir(self.inputdir)

        data = {}
        for f in self.files:
            data = pd.read_excel(join(self.inputdir, f))
            data[f] = data

        self.data = pd.concat(data)


class CosmedFiles(FileParser):

    def __init__(self, inputdir):
        FileParser.__init__(self, inputdir)
        self.inputdir = inputdir
        self.filepattern = '^[:0-9:]{4}[:A-Z:]{2}_\d{1}.*_30sec_[:0-9:]{8}\.xlsx$'

        self.getFiles()
        self.parseFiles()

    def getFiles(self):
        "You need to use absolute paths e.g. with os.path.walk"
        self.files = [join(self.inputdir, f) for f in os.listdir(self.inputdir)
                 if bool(re.match(self.filepattern, basename(f)))]

        self.numberoffiles = len(self.files)
        print('Finished getting files')

    def parseFiles(self):
        "Now you need to be able to parse different types of file patterns"

        files_info = {'Subject': [], 'interval': [] ,'FILE': [], 'PARENT_DIR': []}
        for f in self.files:
            print(('PROCESSING: ' + basename(f)))
            subject = re.findall(self.subjectpattern, basename(f))[0]
            interval = re.findall(self.intervalpattern, basename(f))[0]
            files_info['Subject'].append(subject)
            files_info['interval'].append(int(interval))
            files_info['FILE'].append(basename(f))
            files_info['PARENT_DIR'].append(dirname(f))
            self.files_info = pd.DataFrame.from_dict(files_info).\
                                sort_values(['Subject', 'interval']). \
                                assign(ID=lambda x: x['Subject'].str.slice(0, 4))


class AmunetFiles(FileParser):

    def __init__(self, inputdir):
        FileParser.__init__(self, inputdir)
        self.filepattern = '^.*\.zip$'

        self.getFiles()

    def getFiles(self):
        "You need to use absolute paths e.g. with os.path.walk"
        files = [os.path.join(d, x)
                    for d, dirs, files in os.walk(self.inputdir)
                    for x in files if bool(re.match(self.filepattern, basename(x)))]
        self.files = files
        self.numberoffiles = len(self.files)
        print('Finished getting files')


class BloodFiles:

    def __init__(self, inputdir):
        self.inputdir = inputdir

    def getData(self):

        self.files = os.listdir(self.inputdir)

        bloodsdata = {}
        for f in self.files:
            data = pd.read_excel(join(self.inputdir, f))
            bloodsdata[f] = data


class DexaFiles:

    def __init__(self, inputdir):
        self.inputdir = inputdir
        self.filepattern = '(?m)^(?!(CROSSOVER|CROSS OVER)).*(LS_|LH_|WB_).*$'

        self.getFiles()
        self.parseFiles()


    def getFiles(self):
        files = [os.path.join(d, x)
                 for d, dirs, files in os.walk(self.inputdir)
                 for x in files if bool(re.match(self.filepattern, basename(x)))]

        files = [f for f in files if ('CROSSOVER' not in f and 'CROSS OVER' not in f)]

        self.files = files
        self.numberoffiles = len(self.files)

    def parseFiles(self):
        "Now you need to be able to parse different types of file patterns"

        files_info = {'Subject': [], 'interval': [], 'SCAN_TYPE': [], 'FILE': [], 'DATE_CREATED': [],
                      'LAST_MODIFIED': [], 'PARENT_DIR': []}
        for f in self.files:

            try:
                print(('Parsing %s' % f))
                subject = re.findall("^[:0-9:]{4}[:A-Z:]{2}(?=_)", basename(f))[0]
                interval = re.findall('\d*', basename(dirname(f)))[0]
                date_created = time.ctime(getctime(f))
                date_modified = time.ctime(getmtime(f))
                scan_type = re.findall('(LS|LH|WB)', basename(f))[0]
                files_info['Subject'].append(subject)
                files_info['interval'].append(int(interval))
                files_info['SCAN_TYPE'].append(scan_type)
                files_info['FILE'].append(basename(f))
                files_info['DATE_CREATED'].append(date_created)
                files_info['LAST_MODIFIED'].append(date_modified)
                files_info['PARENT_DIR'].append(dirname(f))

            except ValueError as e:
                print(("ValueError:", e))

        # process files into data.frame
        self.files_info = pd.DataFrame.from_dict(files_info).\
                        sort_values(['Subject', 'interval']). \
                        assign(ID=lambda x: x['Subject'].str.slice(0, 4))


class ValidateFiles:

    def __init__(self, inputdir, type, configfile, sitename='opex'):

        self.inputdir = inputdir
        self.type = type
        self.configfile = configfile
        self.sitename = sitename

        if self.type == 'dexa':
            parser = DexaFiles(inputdir)
            self.compile(parser=parser)
            self.checkDexa()
            self.checkDexaLSLH()

        elif self.type == 'cosmed':
            parser = CosmedFiles(inputdir)
            self.compile(parser=parser)

        elif self.type == 'accelmonthalt':
            parser = AccelFiles(inputdir)
            self.compile(parser=parser)

        elif self.type == 'bloodCobasData':
            parser = BloodFiles(inputdir)
            self.compile(parser=parser)

    def compile(self, parser):

        experiment = 'opex:' + self.type

        print('Compiling Xnat IDs')
        xnat = XnatQuery(listofexperiments=[experiment],
                         configfile=self.configfile,
                         sitename=self.sitename)

        self.matchingfiles = parser.files_info.\
                                merge(xnat.compiler[experiment]['ID'],
                                      how='outer',
                                      on=['ID', 'interval'],
                                      indicator=True)

    def getMismatched(self, on):

        if on == 'filesonly':
            return self.matchingfiles.query('_merge == "left_only"')[['FILE', 'PARENT_DIR']]
        elif on == 'xnatonly':
            return self.matchingfiles.query('_merge == "right_only"')[['ID', 'interval']]

    def summary(self, outputfile):

        self.numberoffiles = self.matchingfiles. \
                                pivot_table(
                                    index=['ID', 'interval'],
                                    values='FILE',
                                    aggfunc=np.size
                                ).unstack('interval')

        self.numberoffiles = self.matchingfiles. \
                                query('_merge == "left_only"'). \
                                    pivot_table(
                                        index=['ID', 'interval'],
                                        values='FILE',
                                        aggfunc=np.size
                                    ).unstack('interval')

        self.filesnotxnat = self.matchingfiles. \
                                    query('_merge == "left_only"'). \
                                    filter(items=['ID',
                                                  'interval',
                                                  'SCAN_TYPE',
                                                  'FILE',
                                                  'PARENT_DIR'], axis=1)

        if outputfile is not None:
            with pd.ExcelWriter(outputfile) as writer:
                self.numberoffiles.to_excel(writer, sheet_name='number_of_files')
                self.filesnotxnat.to_excel(writer, sheet_name='files_not_Xnat')
                self.notxnatnumber.to_excel(writer, sheet_name='number_not_Xnat')

    def checkDexa(self):

        self.filter = {}
        for fil in ['right_only', 'both', 'left_only']:
            self.filter[fil] = self.matchingfiles.\
                            query('_merge == "{}"'.format(fil))[['ID', 'interval']].\
                            drop_duplicates()

        print('# Folders matched to Xnat = %d' % len(self.filter['both']))
        print('# Folders mismatched to Xnat = %d' % len(self.filter['left_only']))
        if len(self.filter['left_only']) > 0:
            print('---------------- List of mismatched folders (not on xnat) ---------------------------')
            print(self.filter['left_only'])

        print('Xnat IDs mismatched to dexa folders %s' % len(self.filter['right_only']))
        if len(self.filter['right_only']) > 0:
            print('---------------- List of mismatched folders (not on xnat) ---------------------------')
            print(self.filter['right_only'])


    def checkDexaLSLH(self):

        hipcols = ['app_lh2',
                   'lh2',
                   'lhip_bmc',
                   'lhip_bmd',
                   'lhip_tscore',
                   'lhip_zscore',
                   'ls_bmc',
                   'ls_bmd',
                   'ls_tscore',
                   'ls_zscore']

        df = XnatQuery(listofexperiments=['opex:dexa'],
                       configfile=configfile,
                       sitename='opex').data[['Subject', 'interval'] + hipcols]

        self.LSLHmissing = self.matchingfiles.dropna()[['Subject', 'interval', 'SCAN_TYPE', 'FILE']]. \
                                pivot_table(

                                    index=['Subject', 'interval'],
                                    values='FILE',
                                    columns='SCAN_TYPE',
                                    aggfunc=np.size,

                                ). \
                                reset_index(). \
                                    merge(df[df.isnull().any(axis=1)][['Subject', 'interval']],
                                          on=['Subject', 'interval'],
                                          how='outer',
                                          indicator=True
                                          ). \
                                    query('_merge in ("right_only")')

        print('------------Accounting for Left hip and Lumbar Spine missing values ----------------------')
        print('Description: LS and LH are not collected at each time point and therefore some fields are missing')
        print('             If this is the case, then we expect the fields missing at given intervals should be missing')
        print('             these files.\n')

        print('Matching Xnat LS/LP fields to files in {}'.format(self.inputdir))

        print('List of Subject-interval IDs with missing LS/LH Xnat fields')

        print(self.LSLHmissing)



#################################################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--expt', action='store', help='Set experiment (dexa, cosmed, accelmonthalt, accelmonth')
    parser.add_argument('--filedir', action='store', help='Change to different directory')

    args = parser.parse_args()

    inputdir_dict = {
        'dexa': 'Q:\\DATA\\DXA Data\\Healthy Brains Exported Data including VAT',
        'accelmonthalt': 'Q:\\DATA\\ActiLife\\agdfiles - Copy',
        'cosmed': 'Q:\\DATA\\COSMEDdata\\30sec',
        'amunetall': 'Q:\\DATA\\DATA ENTRY\\hMWM results'
    }

    # parameters -----------------------------------------------------------------------------------------------
    home = expanduser("~")
    configfile = join(home, '.xnat.cfg')

    experiment = args.expt

    if args.filedir is not None:
        inputdir = args.filedir

    else:
        inputdir = inputdir_dict[experiment]

    # run -------------------------------------------------------------------------------------------------------
    VFiles = ValidateFiles(inputdir=inputdir, type=experiment, configfile=configfile, sitename='opex')

    totalfiles = '# Files = %d' % len(VFiles.matchingfiles)
    numberofmatchedfiles = '# Files matched to Xnat = %d' % len(VFiles.matchingfiles.query('_merge == "both"'))
    numberofmismatchedfiles = '# Files not matched to Xnat = %d' % len(VFiles.getMismatched(on='filesonly'))
    numberofxnatmismatches = '# Xnat Entries not matched to Files = %d' % len(VFiles.getMismatched(on='xnatonly'))

    print(totalfiles)
    print(numberofmatchedfiles)
    print(numberofmismatchedfiles)
    print(numberofxnatmismatches)

    if len(VFiles.getMismatched(on='filesonly')) > 0:
        print('---------------- List of mismatched files (not on xnat) ---------------------------')
        print(VFiles.getMismatched(on='filesonly'))

    if len(VFiles.getMismatched(on='xnatonly')) > 0:
        print('---------------- List of Xnat entries with no matching files ----------------------')
        print(VFiles.getMismatched(on='xnatonly'))

