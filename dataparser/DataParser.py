# -*- coding: utf-8 -*-
"""
Utility script: DataParser - Abstract class
Reads an excel or csv file with data and extracts per subject
run from console/terminal with (example):
>python DataParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
from datetime import datetime
from os import R_OK, access
from os.path import join, basename, splitext, dirname, abspath

import pandas
import logging


class DataParser(object):
    def __init__(self, datafile, sheet=0,skiplines=0, header=None):
        self.datafile = datafile #full pathname to data file
        self.resource_dir = self.__findResourcesdir()
        self.opex = pandas.read_csv(join(self.resource_dir, 'opex.csv'))
        self.incorrect = pandas.read_csv(join(self.resource_dir, 'incorrectIds.csv'))
        if (datafile is not None and len(datafile)> 0):
            (bname, extn)= splitext(basename(datafile))
            self.type = extn #extension - xlsx or csv
            self.sheet = sheet
            self.skiplines = skiplines
            self.header = header
            self._loadData()

    def __findResourcesdir(self):
        resource_dir = glob.glob(join(dirname(__file__), "resources"))
        middir = ".."
        ctr = 1
        while len(resource_dir) <= 0 and ctr < 5:
            resource_dir = glob.glob(join(dirname(__file__), middir, "resources"))
            middir = join(middir, "..")
            ctr += 1
        return abspath(resource_dir[0])

    def __checkSID(self,sid):
        rsid = sid
        if not self.incorrect.empty:
            r = self.incorrect[self.incorrect.INCORRECT == sid]
            if not r.empty:
                rsid = r.CORRECT.values[0]
                msg ='Subject: %s corrected to %s' % (sid,rsid)
                logging.warning(msg)
        return rsid

    def _loadData(self):
        if self.type =='.xlsx' or self.type == '.xls':
            if self.header is None:
                self.data = pandas.read_excel(self.datafile, skiprows=self.skiplines, sheetname=self.sheet, skip_blank_lines=True)
            else:
                self.data = pandas.read_excel(self.datafile, skiprows=self.skiplines, sheetname=self.sheet,
                                              skip_blank_lines=True, header=self.header)
        elif self.type == '.csv':
            self.data = pandas.read_csv(self.datafile, skip_blank_lines=True)
        else:
            self.data = None
        if self.data is not None:
            print('Data loaded')
            self.data.dropna(how="all", axis=0, inplace=True)  # cleanup if rows are all NaN
            self.data.fillna("")  # replace remaining NaNs with empty string
        else:
            print('No data to load')

    def sortSubjects(self):
        '''TO implement by extending class'''
        self.subjects = dict()

    def formatDobNumber(self, orig):
        """
        Reformats DOB string from Excel data float to yyyy-mm-dd
        """
        dateoffset = 693594
        dt = datetime.fromordinal(dateoffset + int(orig))
        return dt.strftime("%Y-%m-%d")

    def formatCondensedDate(self, orig):
        """
        Reformats date number from Excel to yyyymmdd
        """
        dateoffset = 693594
        dt = datetime.fromordinal(dateoffset + int(orig))
        return dt.strftime("%Y%m%d")


def convertExcelDate(orig):
    """
    Reformats date number from Excel to datetime
    """
    # from datetime import datetime
    dateoffset = 693594
    dt = datetime.fromordinal(dateoffset + int(orig))
    return dt

def stripspaces(row,column):
    """
    Strips out whitespace before, within, after a value in column of row
    :param row:
    :param column:
    :return:
    """
    val = str(row[column])
    return val.replace(" ",'')
########################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Parse Water Maze (Amunet) Files',
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="..\\sampledata\\cantab")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract', default="1")
    args = parser.parse_args()

    inputdir = args.filedir
    outputfile = args.report
    sheet = args.sheet
    print("Input:", inputdir)
    if access(inputdir, R_OK):
        seriespattern = '*.*'

        try:
            files = glob.glob(join(inputdir, seriespattern))
            print("Files:", len(files))
            for f2 in files:
                print("Loading", f2)
                dp = DataParser(f2, sheet)
                dp.sortSubjects()
                print('Subject summary:', len(dp.subjects))

        except ValueError as e:
            print("Sheet not found: ", e)

        except:
            raise OSError

    else:
        print("Cannot access directory: ", inputdir)
