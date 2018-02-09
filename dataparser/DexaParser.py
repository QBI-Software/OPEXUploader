# -*- coding: utf-8 -*-
"""
Utility script: DexaParser
Reads an excel or csv file with MRI analysis data and extracts per subject
run from console/terminal with (example):
>python DexaParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
from os import R_OK, access
from os.path import join

import numpy as np
import pandas as pd

from dataparser.DataParser import DataParser, stripspaces

VERBOSE = 0

class DexaParser(DataParser):
    def __init__(self, fields, *args):
        DataParser.__init__(self, *args)
        #Replace field headers
        if access(fields, R_OK):
            self.fields = pd.read_excel(fields, header=0, sheetname='dexa_fields')
            df_header = pd.read_excel(fields, header=0, sheetname='dexa_header')
            self.header = df_header['concatenated'].tolist()
            self.data.columns = self.header
            print("Loaded rows=", len(self.data['ID']))
            #extract subject info
            df_subj = self.data.iloc[:,0:4]
            df_subj['SubjectID'] = df_subj.apply(lambda x: stripspaces(x, 'ID'), axis=1)
            #Split data into intervals
            self.intervals = {0:'BASELINE', 3:'MIDPOINT',6:'ENDPOINT', 9:'MID-FOLLOW-UP', 12:'FOLLOW-UP'}
            self.df = dict()
            for i,intval in self.intervals.items():
                cols = [c for c in self.header if c.startswith(intval)]
                simplecols = []
                for col in cols:
                    cparts = col.split("_")
                    simplecols.append("_".join(cparts[1:]))
                self.df[i] = pd.concat([df_subj,self.data[cols]], axis=1)
                self.df[i].columns = df_subj.columns.tolist() + simplecols
                #self.df[i].reindex(df_subj.columns.tolist() + simplecols, fill_value='')
                if VERBOSE:
                    print("Interval=%s \n\t%s" % (intval, self.df[i].head()))
            #self.sortSubjects()
        else:
            raise ValueError("Cannot access fields file: %s" % fields)

    def sortSubjects(self, subjectfield='SubjectID'):
        '''Sort data into subjects by participant ID'''
        self.subjects = dict()
        if self.df is not None:
            sids = self.df[0][subjectfield].unique()
            ids = [i for i in sids if len(i) == 6]
            for sid in ids:
                sidkey = self._DataParser__checkSID(sid)
                self.subjects[sidkey] = dict()
                for i, intval in self.intervals.items():
                    data = self.df[i]
                    self.subjects[sidkey][i]= data[data[subjectfield] == sid]
                if VERBOSE:
                    print('Subject:', sid, 'with datasets=', len(self.subjects[sid]))
            print('Subjects loaded=', len(self.subjects))


    def getSampleid(self, sd, interval):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'DXA_' + sd + '_' + str(interval)
        return id

    def getxsd(self):
        xsd = 'opex:dexa'
        return xsd

    def mapData(self, row, i, xsd):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """

        mandata = {
            xsd + '/interval': str(i),
            xsd + '/sample_id': str(row.index.values[0]),  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': self.intervals[i]
        }
        motdata = {}
        for i in range(len(self.fields)):
            field = self.fields['Field'][i]
            xnatfield = self.fields['XnatField'][i]
            if field in row and not np.isnan(row[field].iloc[0]):
                motdata[xsd + '/' + xnatfield] = str(row[field].iloc[0])
        return (mandata, motdata)



########################################################################

if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files', default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\dexa")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    parser.add_argument('--fields', action='store', help='Fields to extract',
                        default="..\\resources\\dexa_fields.xlsx")
    args = parser.parse_args()

    inputdir = args.filedir
    sheet = int(args.sheet)
    fields = args.fields
    skip = 4
    print("Input:", inputdir)
    if access(inputdir, R_OK):
        seriespattern = 'DXA Data entry*.xlsx'
        try:
            files = glob.glob(join(inputdir, seriespattern))
            print "Files:", len(files)
            for f2 in files:
                print "Loading ", f2
                dp = DexaParser(fields, f2, sheet, skip)
                xsdtypes = dp.getxsd()
                dp.sortSubjects()
                for sd in dp.subjects:
                    print '\n***********SubjectID:', sd
                    for i, row in dp.subjects[sd].items():
                        print 'Interval:', dp.intervals[i]
                        sampleid = dp.getSampleid(sd, i)
                        print 'Sampleid:', sampleid
                        (mandata, data) = dp.mapData(row, i, xsdtypes)
                        print mandata
                        print data
                        # for field in dp.fields['Field']:
                        #     if field in row and not np.isnan(row[field].iloc[0]):
                        #         print field, "=", row[field].iloc[0]



        except Exception as e:
            print("Error: ", e)

    else:
        print("Cannot access directory: ", inputdir)
