# -*- coding: utf-8 -*-
"""
Utility script: AmunetParser
Reads an excel or csv file with data and extracts per subject
run from console/terminal with (example):
>python AmunetParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import csv
import fnmatch
import glob
import logging
import re
import os
import shutil
from datetime import date
from os import listdir, R_OK, access
from os.path import join, isfile, split, basename

import pandas
from numpy import nan
from pandas import Series
import sys

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser

VERBOSE = 0


class AmunetParser(DataParser):

    def __init__(self, *args):
        # super(AmunetParser, self).__init__(*args) - PYTHON V3
        DataParser.__init__(self, *args)
        self.dates = dict()
        self.subjects = dict()
        self.interval = None
        self.sortSubjects()

    def sortSubjects(self, subjectfield='S_Full name'):
        '''Sort data into subjects by participant ID'''
        if self.data is not None:
            ids = self.data[subjectfield].unique()
            # Load extra info from dir name and generated participant dates
            if self.interval is not None:
                self.data['Visit'] = self.data.apply(lambda x: self.interval, axis=1)
                pdatefile = self.interval + 'm_amunet_participantdates.csv'
                self.inputdir = split(self.datafile)[0]
                pdates = pandas.read_csv(join(self.inputdir, pdatefile), header=None)
                pdates.columns = ['subject', 'visit']
                self.data['Date'] = self.data.apply(lambda x: self.getRowvisit(x, pdates), axis=1)
            for sid in ids:
                sidkey = self._DataParser__checkSID(sid)
                self.subjects[sidkey] = self.data[self.data[subjectfield] == sid]
                if VERBOSE:
                    print(('Subject:', sid, 'with datasets=', len(self.subjects[sid])))
            print(('Subjects loaded=', len(self.subjects)))

    def getRowvisit(self, row, pdates):
        d = pdates['visit'][pdates['subject'] == row['S_Full name']]
        if d is None or d.empty:
            rtn = ''
        else:
            rtn = d.values[0]
        return rtn

    def getxsd(self):
        return 'opex:amunet'

    def mapMandata(self, xsd, row, i):
        # Get Visit if present (manual)
        if ('Visit' in row and row.Visit is not None):
            interval = int(row['Visit'])
        elif row['S_Visit'] is not None:  # No overwrite
            visit = re.search('Visit\s(\d{1,2})', str(row['S_Visit']))
            interval = int(visit.group(1))
            if interval == 1:
                interval = 0
        else:
            interval = 0
        visitdate = self.getVisitDate(row)

        mandata = {
            xsd + '/interval': str(interval),
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial'
        }
        if (visitdate is not None):
            mandata[xsd + '/date'] = visitdate
        return mandata

    def getVisitDate(self, row):
        """
        Gets visit date in correct format for uploading
        :param row: reads field "Date" as yyyy-mm-dd
        :return: string as yyyy.mm.dd 00:00:00
        """
        # Get Date if present (manual)
        visitdate = None
        if ('Date' in row):
            try:
                visitdate = int(row['Date'])
                visitdate = self.formatDobNumber(visitdate)
            except:
                visitdate = row['Date']  # .replace("-",".")
                # visitdate = visitdate + " 00:00:00"
        print(("Visit date=", visitdate))
        return visitdate

    def mapAEVdata(self, row, i):
        """
        Maps required fields from input rows
        :param row:
        :return:
        """
        xsd = self.getxsd()
        mandata = self.mapMandata(xsd, row, i)
        # visitdate = self.getVisitDate(row)

        data = {
            xsd + '/AEVcomments': str(row['AEV_Lexical rating']),
            xsd + '/AEV': str(row['AEV_Average total error']),
            xsd + '/EV': str(row['EV_Average total error']),
            xsd + '/AV': str(row['AV_Average total error']),
            xsd + '/DV': str(row['DV_Average total error'])

        }

        return (mandata, data)

    def mapSCSdata(self, row, i):
        """
        Maps required fields from input row
        :param self:
        :param row:
        :return:
        """
        xsd = self.getxsd()
        mandata = self.mapMandata(xsd, row, i)
        # visitdate = self.getVisitDate(row)
        data = {
            xsd + '/SCScomments': str(row['SCS_Lexical rating']),
            xsd + '/SCS': str(row['SCS_Average total error']),
            xsd + '/SCD': str(row['SCD_Average total error']),
            xsd + '/SAS': str(row['SAS_Average total error']),
            xsd + '/SAD': str(row['SAD_Average total error']),
            xsd + '/SES': str(row['SES_Average total error']),
            xsd + '/SED': str(row['SED_Average total error'])
        }
        # if (visitdate is not None):
        #     data[xsd + '/date'] = visitdate
        return (mandata, data)

    def getSubjectData(self, sd):
        """
        Extract subject data from input data
        :param sd:
        :return:
        """
        skwargs = {}
        if self.subjects is not None:
            dob = self.formatDobNumber(self.subjects[sd]['S_Date of birth'].iloc[0])
            gender = str(self.subjects[sd]['S_Sex'].iloc[0]).lower()
            hand = str(self.subjects[sd]['S_Hand'].iloc[0])
            skwargs = {'dob': dob}
            if gender in ['female', 'male']:
                skwargs['gender'] = gender
            if hand in ['Right', 'Left', 'Ambidextrous']:
                skwargs['handedness'] = hand

        return skwargs

    def getSampleid(self, sd, row):
        """
        Generate a unique id for Amunet sample which can be reproduced if this data reoccurs
        :param row:
        :return:
        """
        # visit = re.search('Visit\s(\d{1,2})', str(row['S_Visit']))
        if ('Date' in row):
            try:
                uid = int(row['Date'])
                uid = self.formatCondensedDate(uid)
            except:
                uid = row['Date'].replace('-', '')
        else:
            uid = sum([i for i in row if type(i) == float])  # create hash of values from row values
            uid = int(uid)
        id = "AM_" + sd + "_" + str(uid)
        return id

    def extractDateInfo(self, dirpath):
        seriespattern = '*.zip'
        zipfiles = [f for f in listdir(dirpath) if (isfile(join(dirpath, f)) and fnmatch.fnmatch(f, seriespattern))]
        print(zipfiles)
        rid = re.compile('^(\d{4}.{2})')
        rdate = re.compile('(\d{8})\.zip$')
        for f in zipfiles:
            fid = rid.search(f).group(0).upper()
            fdate = rdate.search(f).groups()[0]
            # some dates are in reverse
            try:
                if (fdate[4:6]) == '20':
                    fdateobj = date(int(fdate[4:9]), int(fdate[2:4]), int(fdate[0:2]))
                else:
                    fdateobj = date(int(fdate[0:4]), int(fdate[4:6]), int(fdate[6:9]))
            except ValueError:
                print(("cannot create date from: ", fdate))
                continue

            if self.dates.get(fid) is not None:
                self.dates[fid].append(fdateobj)
            else:
                self.dates[fid] = [fdateobj]

        print((self.dates))
        # Output to a csvfile
        csvfile = join(dirpath, 'amunet_participantdates.csv')
        with open(csvfile, 'wb') as f:
            writer = csv.writer(f)
            for d in self.dates:
                vdates = pandas.Series(self.dates[d])
                self.dates[d] = vdates.unique()
                writer.writerow([d, [v.isoformat() for v in self.dates[d]]])


# ---------EXTERNAL FUNCTION------------------------------------------------------
def generateAmunetdates(dirpath, filename, interval):
    """
    Generate dates for amunet data from files
    config in txt file in local dir
    :param dirpath:
    :param filename:
    :param interval:
    :return:
    """
    csvfile=None
    if access(dirpath, R_OK):
        pdates = extractDateInfo(dirpath, ext='zip')
        # Output to a csvfile
        csvfile = join(dirpath, interval + 'm_' + filename)
        try:
            with open(csvfile, 'wb') as f:
                writer = csv.writer(f)
                for d in pdates:
                    vdates = Series(pdates[d])
                    vdates = vdates.unique()
                    writer.writerow([d, ",".join([v.isoformat() for v in vdates])])
                msg = "Participant dates written to: %s" % csvfile
                logging.info(msg)
                print("Generate Amunet Dates Finished")
        except Exception as e:
            print(e)
            raise ValueError( e)
    else:
        msg = "Cannot access amunet directory: %s" % dirpath
        raise IOError(msg)

    return csvfile


# ------------------------------------------------------------------------------------
def extractDateInfo(dirpath, ext='zip'):
    """
    Extract date from filenames with ext
    :param dirpath: directory with files
    :param ext: extension of files to filter
    :return: list of participants with dates in sequence
    """
    participantdates = dict()
    seriespattern = '*.' + ext
    zipfiles = glob.glob(join(dirpath, seriespattern))
    print(("Total files: ", len(zipfiles)))
    # Extract date from filename - expect
    rid = re.compile('^(\d{4}.{2})')
    rdate = re.compile('(\d{8})\.zip$')
    for filename in zipfiles:
        f = basename(filename)

        # some dates are in reverse
        try:
            if (rid.search(f) and rdate.search(f)):
                fid = rid.search(f).group(0).upper()
                fdate = rdate.search(f).groups()[0]
                if (fdate[4:6]) == '20':
                    fdateobj = date(int(fdate[4:9]), int(fdate[2:4]), int(fdate[0:2]))
                else:
                    fdateobj = date(int(fdate[0:4]), int(fdate[4:6]), int(fdate[6:9]))
            else:
                continue
        except ValueError as e:
            msg = "Error: %s: %s" % (e, f)
            raise ValueError(msg)

        if participantdates.get(fid) is not None:
            participantdates[fid].append(fdateobj)
        else:
            participantdates[fid] = [fdateobj]

    print(("Loaded:", len(participantdates)))
    return participantdates

########################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Parse Water Maze (Amunet) Files',
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\amunet")
    # parser.add_argument('--datelist', action='store', help='Generate list of dates from dir', default="1")

    args = parser.parse_args()
    sheet = 0
    topinputdir = args.filedir
    basedatesfile = 'amunet_participantdates.csv'
    seriespattern = '*.xlsx'
    subdirs = listdir(topinputdir)
    print('Finding dates from subdirectories')
    for inputdir in subdirs:
        if inputdir not in ['0m', '3m', '6m', '9m', '12m']:
            continue
        interval = inputdir[0:-1]
        print('Interval:', interval)
        inputdir = join(topinputdir, inputdir)
        print(inputdir)
        # Get dates from zip files
        dates_uri_file = join(inputdir, 'folderpath.txt')
        with open(dates_uri_file, "r") as dd:
            content = dd.readlines()
            for line in content:
                dates_uri = line.strip()
                break
        if len(dates_uri) <= 0:
            raise ValueError('No dates file found - exiting')
        dates_csv = generateAmunetdates(dates_uri, basedatesfile, interval)
        # copy file to this dir
        shutil.copyfile(dates_csv, join(inputdir, basename(dates_csv)))
        # Get xls files
        files = glob.glob(join(inputdir, seriespattern))
        print(("Loading Files:", len(files)))
        for f2 in files:
            print(("Loading", f2))
            dp = AmunetParser(interval, f2, sheet)
            xsdtypes = dp.getxsd()
            # dp.interval = interval
            for sd in dp.subjects:
                print(('\n*****SubjectID:', sd))
                for i, row in dp.subjects[sd].iterrows():
                    sampleid = dp.getSampleid(sd, row)
                    row.replace(nan, '', inplace=True)
                    print(('Sampleid:', sampleid))
                    if 'AEV_Average total error' in row:
                        (mandata, motdata) = dp.mapAEVdata(row, i)
                    else:
                        (mandata, motdata) = dp.mapSCSdata(row, i)
                    print(mandata)
                    print(motdata)
