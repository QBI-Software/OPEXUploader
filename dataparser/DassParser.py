# -*- coding: utf-8 -*-
"""
Utility script: DassParser
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

class DassParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        #Replace field headers
        self.fields = ['depression', 'anxiety', 'stress']
        ncols=[]
        for ix in range(0,13,3):
            ncols += [c + '_'+str(ix) for c in self.fields]

        dropcols=[] #remove check columns
        for n in range(3, len(self.data.columns), 12):
            start = n
            end = n + 9
            #print 'Drop ', start, ' to ', end
            #print self.data.columns.tolist()[start:end]
            dropcols += self.data.columns.tolist()[start:end]
        #print dropcols
        df = self.data.drop(columns=dropcols)
        df.columns=ncols
        df.reindex()
        self.data=df
        #sort subjects
        self.data['SubjectID'] = self.data.index
        self.sortSubjects('SubjectID')
        print 'Data load complete'



    def getSampleid(self, sd, interval):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'DASS_' + sd + '_' + str(interval)+'M'
        return id

    def getxsd(self):
        xsd = 'opex:dass'
        return xsd

    def mapData(self, row, i, xsd):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """

        mandata = {
            xsd + '/interval': str(i),
            xsd + '/sample_id':'',  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': ''
        }
        motdata = {}
        totalcols = 0
        for field in self.fields:
            rfield = field + '_' + str(i)
            if rfield in row and not np.isnan(row[rfield].iloc[0]):
                motdata[xsd + '/' + field] = str(row[rfield].iloc[0])
                totalcols += row[rfield].iloc[0]
        motdata[xsd + '/total'] = str(totalcols)
        return (mandata, motdata)

    def validData(self,dvalues):
        """
        Checks data is present in list
        -	-	-

        :param dvalues:
        :return:
        """
        rtn = True
        if isinstance(dvalues,list):
            for d in dvalues:
                if isinstance(d,str) or isinstance(d,unicode) or np.isnan(d):
                    rtn = False
                    break

        return rtn

########################################################################

if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files', default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\DASS")
    parser.add_argument('--datafile', action='store', help='Filename of original data', default="DASS Data Entry Plus Check_20171206.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputfile = join(args.filedir, args.datafile)
    sheet = int(args.sheet)
    skip = 0
    header =2
    print("Input:", inputfile)
    if access(inputfile, R_OK):
        try:
            print "Loading ", inputfile
            dp = DassParser(inputfile, sheet, skip, header)
            xsdtypes = dp.getxsd()
            intervals = range(0,13,3)
            for sd in dp.subjects:
                print '\n***********SubjectID:', sd
                for i in intervals:
                    print 'Interval:', i
                    iheaders = [c + "_"+str(i) for c in dp.fields]
                    sampleid = dp.getSampleid(sd, i)
                    print 'Sampleid:', sampleid
                    row = dp.subjects[sd]
                    if not dp.validData(row[iheaders].values.tolist()[0]):
                        print 'empty data - skipping'
                        continue
                    (mandata, data) = dp.mapData(row[iheaders], i, xsdtypes)
                    print mandata
                    print data

        except Exception as e:
            print("Error: ", e)

    else:
        print("Cannot access file: ", inputfile)
