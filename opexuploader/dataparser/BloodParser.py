# -*- coding: utf-8 -*-
"""
Utility script: BloodParser
Reads an excel or csv file with data and extracts per subject
run from console/terminal with (example):
>python BloodParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""
from __future__ import print_function

import argparse
import glob
import os
import sys
from datetime import datetime
from os import R_OK, access
from os.path import join

import pandas

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser

DEBUG = 0


class BloodParser(DataParser):

    def __init__(self, *args, **kwargs):
        DataParser.__init__(self, *args)
        if self.data is None:
            raise ValueError('BloodParser: Data not loaded')
        self.type = ''
        if 'type' in kwargs:
            self.type = kwargs.get('type')
            self.fields = self.dbi.getFields(self.type)
            self.info = self.dbi.getInfo(self.type)
            # self.fields = self.getFieldsFromFile(self.type)

        elif self.etype is not None:
            self.type = self.etype
        print('Rename Headers for ', self.type)
        ## Rename columns in dataframe
        if self.type == 'IGF':
            colnames = {'Date': 'A_Date',
                        'Participant ID ': 'Participant ID',
                        'Timepoint': 'Sample ID',
                        'IGF-1': 'IGF1'}
            self.data = self.data.rename(index=str, columns=colnames)

        elif self.type == 'SOMATO':
            colnames = {'Date': 'A_Date',
                        'Participant ID ': 'Participant ID',
                        'Timepoint': 'Sample ID',
                        'Somatostatin': 'somatostatin'}
            self.data = self.data.rename(index=str, columns=colnames)

        elif self.type == 'BDNF':
            colnames = {'Date': 'A_Date',
                        'Participant ID ': 'Participant ID',
                        'Timepoint': 'Sample ID'}
            self.data = self.data.rename(index=str, columns=colnames)

        elif self.type == 'MULTIPLEX':
            colnames = {'Date': 'A_Date',
                        'Participant ID ': 'Participant ID',
                        'Timepoint': 'Sample ID',
                        'IGFBP-7': 'IGFBP7'}
            self.data = self.data.rename(index=str, columns=colnames)

        elif self.type == 'INFLAM':
            print('Headers for ', self.type)
            colnames = {'Date': 'A_Date',
                        'Participant ID ': 'Participant ID',
                        'Timepoint': 'Sample ID',
                        u'IFN\u03b3': 'ifngamma',
                        'IL-10': 'il10',
                        'IL-12(p70)': 'il12p70',
                        u'IL-1\u03b2': 'il1beta',
                        'IL-6': 'il6',
                        'IL-8': 'il8cxcl8',
                        u'TNF\u03B1': 'tnfalpha'
                        }
            self.data = self.data.rename(index=str, columns=colnames)

        elif self.type == 'ELISAS':
            colnames = {'Date': 'A_Date',
                        'Participant ID ': 'Participant ID',
                        'Timepoint': 'Sample ID',
                        'Beta-H (ng/ul)': 'BetaHydroxy'}
            self.data = self.data.rename(index=str, columns=colnames)

        elif self.type == 'COBAS':
            # Name unnamed columns to field names
            if self.fields[0] not in self.data.columns:
                colnames = {}
                v = 1
                for i in range(len(self.fields)):
                    colnames['Value.' + str(v)] = self.fields[i]
                    v = v + 2
            else:
                colnames = {'Date': 'A_Date',
                            'Participant ID ': 'Participant ID',
                            'Timepoint': 'Sample ID',
                            'Prolactin': 'Prolactin',
                            'Insulin': 'Insulin',
                            'HGH': 'HGH',
                            'Cortisol': 'Cortisol'}

            self.data = self.data.rename(index=str, columns=colnames)
        print('Colnames: ', self.data.columns.tolist())
        # Insert Row Number column
        if 'R_No.' not in self.data.columns:
            self.data.insert(0, 'R_No.', list(range(len(self.data))))

        # Remove NaT rows
        i = self.data.query('A_Date =="NaT"')
        if not i.empty:
            self.data.drop(i.index[0], inplace=True)
            print('NaT row dropped')

        # Organize data into subjects
        subjectfield = 'Participant ID'
        if subjectfield not in self.data.columns:
            raise ValueError('Subject ID field not present: ', subjectfield)
        self.data[subjectfield] = self.data[subjectfield].str.replace(" ", "")
        self.sortSubjects(subjectfield)
        if self.subjects is not None:
            print('BloodParser: subjects loaded successfully')
        self.subjectfield = subjectfield

    # def getInterval(self, rowval):
    #     print('getinterval', rowval)

    def getFieldsFromFile(self, type):
        """
        Get list of fields for subtype
        :param self:
        :return:
        """
        fields = []
        try:
            fieldsfile = join(self.resource_dir, 'blood_fields.csv')
            df = pandas.read_csv(fieldsfile, header=0)
            fields = df[self.type]
            fields.dropna(inplace=True)
        except Exception as e:
            raise e
        return fields

    def getPrepostOptions(self, i):
        options = ['fasted', 'pre', 'post']
        return options[i]

    def parseSampleID(self, sampleid):
        """
        Splits sample id
        :param sampleid: 0-0-S-a gives interval-prepost-S-a
        :return: interval, prepost string
        """
        parts = sampleid.split("-")
        if len(parts) == 4:
            interval = int(parts[0])
            prepost = self.getPrepostOptions(int(parts[1]))
        else:
            interval = -1
            prepost = ""
        return (interval, prepost)

    def getSampleid(self, sd, row):
        """
        Generate a unique id for data sample
        :param row:
        :return:
        """
        if 'Sample ID' in row:
            parts = row['Sample ID'].split("-")
            id = "%s_%dm_%s_%d" % (sd, int(parts[0]), self.getPrepostOptions(int(parts[1])), int(row['R_No.']))

        else:
            raise ValueError("Sample ID column missing")
        return id

    def formatADate(self, orig):
        """
        Formats date from input as dd/mm/yyyy hh:mm:ss
        :param orig:
        :return:
        """
        if isinstance(orig, pandas.Timestamp) or isinstance(orig, datetime):
            dt = orig
        elif "/" in orig:
            dt = datetime.strptime(orig, "%d/%m/%Y %H:%M:%S")
        elif "-" in orig:
            dt = datetime.strptime(orig, "%Y-%m-%d %H:%M:%S")
        else:
            dt = orig
        return dt.strftime("%Y.%m.%d %H:%M:%S")

    def getxsd(self):
        xsd = {'MULTIPLEX': 'opex:bloodMultiplexData',
               'BDNF': 'opex:bloodBdnfData',
               'COBAS': 'opex:bloodCobasData',
               'ELISAS': 'opex:bloodElisasData',
               'INFLAM': 'opex:bloodInflamData',
               'IGF': 'opex:bloodIgfData',
               'SOMATO': 'opex:bloodSomatostatinData'}
        return xsd[self.type]

    def mapData(self, row, i, xsd=None):
        """
        Maps required fields from input rows
        :param row:
        :return:
        """
        (interval, prepost) = self.parseSampleID(row['Sample ID'])

        if xsd is None:
            xsd = self.getxsd()

        mandata = {
            xsd + '/interval': str(interval),
            xsd + '/sample_id': row['Sample ID'],  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial',
            xsd + '/date': self.formatADate(row['A_Date']),
            xsd + '/comments': 'Date analysed not collected',
            xsd + '/prepost': prepost,
            xsd + '/sample_num': str(row['R_No.'])

        }
        # Different fields for different bloods
        data = {}
        for ctab in self.fields:
            if ctab in row:
                if DEBUG:
                    print(ctab, ' = ', row[ctab])
                data[xsd + '/' + ctab] = str(row[ctab])

        return (mandata, data)


########################################################################

if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')
    TEST_TYPE = 'INFLAM'
    TEST_DIR = '../../data/'


    parser.add_argument('--filedir', action='store', help='Directory containing files', default=TEST_DIR)
    parser.add_argument('--sheet', action='store', help='Sheet name to extract', default="0")
    parser.add_argument('--type', action='store', help='Type of blood sample', default=TEST_TYPE)
    args = parser.parse_args()

    inputdir = args.filedir + TEST_TYPE
    header = None
    etype = args.type
    # Set Excel sheet no
    sheet = int(args.sheet)
    # Skip x rows in Excel sheet before data
    skip = 0  # DEFAULT
    if args.type == 'COBAS':
        skip = 1
    elif args.type == 'ELISAS' or args.type == 'SOMATO':
        sheet = 2

    print("Input:", inputdir)
    if access(inputdir, R_OK):
        seriespattern = '*.xlsx'

        try:
            files = glob.glob(join(inputdir, seriespattern))
            print("Files:", len(files))
            for f2 in files:
                print("\n****Loading", f2)
                dp = BloodParser(f2, sheet, skip, header, etype)

                for sd in dp.subjects:
                    print('ID:', sd)
                    for i, row in dp.subjects[sd].iterrows():
                        # dob = dp.formatADate(str(dp.subjects[sd]['A_Date'][i]))
                        # uid = dp.type + "_" + dp.getSampleid(sd, row)
                        # print(i, 'Visit:', uid, 'Date', dob)
                        (d1, d2) = dp.mapData(row, i)
                        # print(d1)
                        print(d2)
        except ValueError as e:
            print(e)
    else:
        print("Cannot access directory: ", inputdir)
