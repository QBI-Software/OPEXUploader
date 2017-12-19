# -*- coding: utf-8 -*-
"""
Utility script: MridataParser
Reads an excel or csv file with MRI analysis data and extracts per subject
run from console/terminal with (example):
>python MridataParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
from datetime import datetime
from os import R_OK, access
from os.path import join

import pandas

from dataparser.DataParser import DataParser

VERBOSE = 0
class MridataParser(DataParser):
    def __init__(self, fields, *args):
        DataParser.__init__(self, *args)
        if 'ASHS' in self.datafile:
            self.type = 'ASHS'
        elif 'FreeSurf' in self.datafile:
            self.type = 'FS'
        else:
            raise ValueError("Cannot determine MRI type")
        try:
            access(fields, R_OK)
            df = pandas.read_csv(fields, header=0)
            self.cantabfields = df[self.type]
        except:
            raise ValueError("Cannot access fields")

    def sortSubjects(self):
        '''Sort data into subjects by participant ID'''
        self.subjects = dict()
        if self.data is not None:
            ids = self.data['Subject'].unique()
            for sid in ids:
                self.subjects[sid] = self.data[self.data['Subject'] == sid]
                if VERBOSE:
                    print('Subject:', sid, 'with datasets=', len(self.subjects[sid]))
            print('Subjects loaded=', len(self.subjects))

    def formatDateString(self, orig):
        '''Reformats datetime string from yyyy.mm.dd hh:mm:ss to yyyy-mm-dd'''
        dt = datetime.strptime(orig, "%Y.%m.%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")

    def getStringDateUTC(self, orig):
        '''Returns datetime string as a unique id'''
        dt = datetime.strptime(orig, "%Y.%m.%d %H:%M:%S UTC")
        return dt.strftime("%Y%m%d%H%M%S")

    def genders(self):
        return {0: 'male', 1: 'female'}

    def formatDob(self, orig):
        """
        Reformats DOB string from yyyy-mm-dd 00:00:00 as returned by series obj to yyyy-mm-dd
        """
        # dt = datetime.strptime(orig,"%d-%b-%y") #if was 20-Oct-50
        # dt = datetime.strptime(orig, "%d/%m/%Y")
        dt = datetime.strptime(orig, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")

    def getInterval(self, orig):
        """Parses string M-00 to 0 or M-01 to 1 etc"""
        interval = int(orig[2:])
        return interval

    def getSampleid(self, sd, row):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        cantabid = sd + '_' + str(row['Visit'])
        return cantabid

    def getxsd(self):
        xsd = {'ASHS': 'opex:mriashs',
               'FS': 'opex:mrifs'
               }
        return xsd

    def mapData(self, row, i, xsd):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """

        mandata = {
            xsd + '/interval': str(row['Visit']),
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial',
            xsd + '/comments': ""
        }
        motdata = {}
        for ctab in self.cantabfields:
            if ctab in row:
                motdata[xsd + '/' + ctab] = str(row[ctab])
        return (mandata, motdata)

    def getSubjectData(self, sd):
        """
        Load subject data from input data
        :param sd:
        :return:
        """
        skwargs = {}
        if self.subjects is not None:
            dob = self.formatDob(str(self.subjects[sd]['Date of Birth'].iloc[0]))
            gender = self.genders()[self.subjects[sd]['Gender'].iloc[0]]
            group = str(self.subjects[sd]['Group'].iloc[0])
            skwargs = {'dob': dob, 'gender': gender, 'group': group}
        return skwargs


########################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Parse MRI Analysis',
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files', default="sampledata\\mridata")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="1")
    parser.add_argument('--fields', action='store', help='MRI fields to extract',
                        default="resources\\MRI_fields.csv")
    args = parser.parse_args()

    inputdir = args.filedir
    sheet = args.sheet
    fields = args.fields
    print("Input:", inputdir)
    if access(inputdir, R_OK):
        seriespattern = '*.*'
        try:
            files = glob.glob(join(inputdir, seriespattern))
            print "Files:", len(files)
            for f2 in files:
                print "Loading ", f2
                cantab = MridataParser(fields, f2, sheet)
                cantab.sortSubjects()
                for sd in cantab.subjects:
                    print '**SubjectID:', sd
                    print "**MRI Fields**"
                    for i, row in cantab.subjects[sd].iterrows():
                        print(i, 'Visit:', row['Visit'])
                        for ctab in cantab.cantabfields:
                            if ctab in row:
                                print ctab, "=", row[ctab]


        except ValueError as e:
            print("Sheet not found: ", e)

        except OSError as e:
            print("OS error:", e)

    else:
        print("Cannot access directory: ", inputdir)
