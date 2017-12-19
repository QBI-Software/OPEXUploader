# -*- coding: utf-8 -*-
"""
Utility script: BloodParser
Reads an excel or csv file with data and extracts per subject
run from console/terminal with (example):
>python BloodParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
from os import R_OK, access
from os.path import join
from datetime import datetime
import pandas
import numpy as np

from dataparser.DataParser import DataParser

VERBOSE = 0
class BloodParser(DataParser):

    def __init__(self, *args, **kwargs):
        DataParser.__init__(self, *args)
        self.type=''
        if 'type' in kwargs:
            self.type = kwargs.get('type')
        if 'fields' in kwargs:
            fields = kwargs.get('fields')
        else:
            fields = 'resources/blood_fields.csv'

        try:
            self.opex = pandas.read_csv(join('resources', 'opex.csv'))
            access(fields, R_OK)
            df = pandas.read_csv(fields, header=0)
            self.fields = df[self.type]
            self.fields.dropna(inplace=True)
            #TODO replace headers with Value.x - true for COBAS data SO FAR
            if self.type =='COBAS':
                colnames = {}
                v=1
                for i in range(len(self.fields)):
                    colnames['Value.' + str(v)] = self.fields[i]
                    v = v + 2

                df = self.data.rename(index=str, columns=colnames)
                print("NB. renamed columns: ", colnames)
                self.data = df

        except:
            raise ValueError("Cannot access fields")

    def sortSubjects(self):
        '''Sort data into subjects by participant ID'''
        self.subjects = dict()
        if self.data is not None:
            self.data['Participant ID'] = self.data['Participant ID'].str.replace(" ","")
            ids = self.data['Participant ID'].unique()
            for sid in ids:
                self.subjects[sid] = self.data[self.data['Participant ID'] == sid]
                if VERBOSE:
                    print 'Subject:', sid, 'with datasets=', len(self.subjects[sid])
            print 'TOTAL Subjects loaded=', len(self.subjects)

    def getxsd(self):
        return {"COBAS":'opex:bloodCobasData',
                "MULTIPLEX": 'opex:bloodMultiplexData',
                "ELISAS": 'opex:bloodElisasData'}

    def getPrepostOptions(self,i):
        options = ['fasted', 'pre', 'post']
        return options[i]

    def parseSampleID(self,sampleid):
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
            id = "%s_%dm_%s_%s" % (sd, int(parts[0]), self.getPrepostOptions(int(parts[1])), row['R_No.'])
        else:
            raise ValueError("Sample ID column missing")
        return id

    def formatADate(self, orig):
        """
        Formats date from input as dd/mm/yyyy hh:mm:ss
        :param orig:
        :return:
        """
        if isinstance(orig, pandas.tslib.Timestamp):
            dt = orig
        elif "/" in orig:
            dt = datetime.strptime(orig, "%d/%m/%Y %H:%M:%S")
        elif "-" in orig:
            dt = datetime.strptime(orig, "%Y-%m-%d %H:%M:%S")
        else:
            dt = orig
        return dt.strftime("%Y.%m.%d %H:%M:%S")

    def mapData(self, row, i, xsd=None):
        """
        Maps required fields from input rows
        :param row:
        :return:
        """
        (interval,prepost) = self.parseSampleID(row['Sample ID'])
        if xsd is None:
            xsd = self.getxsd()[self.type]
        mandata = {
            xsd + '/interval': str(interval),
            xsd + '/sample_id': row['Sample ID'],  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial',
            xsd + '/date' : self.formatADate(row['A_Date']),
            xsd + '/comments' : 'Date analysed not collected',
            xsd + '/prepost': prepost,
            xsd + '/sample_num' : str(row['R_No.'])

        }
        #Different fields for different bloods
        data = {}
        for ctab in self.fields:
            if ctab in row:
                data[xsd + '/' + ctab] = str(row[ctab])

        return (mandata,data)




########################################################################

if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')

    parser.add_argument('--filedir', action='store', help='Directory containing files', default="sampledata\\blood\\COBAS")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract', default="0")
    args = parser.parse_args()

    inputdir = args.filedir
    sheet = int(args.sheet)
    skip = 1
    type = "COBAS"
    print("Input:", inputdir)
    if access(inputdir, R_OK):
        seriespattern = '*.xlsx'

        try:
            files = glob.glob(join(inputdir, seriespattern))
            print("Files:", len(files))
            for f2 in files:
                print "\n****Loading",f2
                dp = BloodParser(f2,sheet,skip, type=type)
                dp.sortSubjects()

                for sd in dp.subjects:
                    print 'ID:', sd
                    for i, row in dp.subjects[sd].iterrows():
                        dob = dp.formatADate(str(dp.subjects[sd]['A_Date'][i]))
                        uid = dp.type + "_" + dp.getSampleid(sd,row)
                        print i, 'Visit:', uid, 'DOB', dob
                        (d1,d2) = dp.mapData(row,i)
                        print d1
                        print d2



        except ValueError as e:
            print(e)

    else:
        print("Cannot access directory: ", inputdir)
