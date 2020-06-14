# -*- coding: utf-8 -*-
"""
Utility script: FitbitParser
Reads an excel or csv file with MRI analysis data and extracts per subject
run from console/terminal with (example):
>python DexaParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import os
from os import R_OK, access
from os.path import join

import numpy as np
import sys

sys.path.append(os.getcwd())
# from DataParser import DataParser

from opexuploader.dataparser.abstract.DataParser import DataParser

VERBOSE = 0

class FitbitParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        #Replace field headers
        self.fields = ['calories_burned', 'steps', 'distance', 'floors', 'min_sed', 'min_lightact','min_fairact', 'min_veryact', 'act_calories']
        self.sortSubjects('Subject')
        print('Data load complete')

    def getSampleid(self, sd, interval):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'FITBIT_' + sd + '_' + str(interval)+'M'
        return id

    def getxsd(self):
        xsd = 'opex:fitbit'
        return xsd

    def mapData(self, row, i, xsd=None):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """

        if xsd is None:
            xsd = self.getxsd()

        mandata = {
            xsd + '/interval': str(int(row['interval'])),
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': ''
        }
        motdata = {}
        for field in self.fields:
            if field in row and not np.isnan(row[field]):
                motdata[xsd + '/' + field] = str(row[field])

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
                if isinstance(d,str) or isinstance(d,str) or np.isnan(d):
                    rtn = False
                    break

        return rtn

#############################################################################
if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files', default="Q:\\DATA\\FITBIT DATA")
    parser.add_argument('--datafile', action='store', help='Filename of original data', default="sum_fitbit.csv")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputfile = join(args.filedir, args.datafile)
    sheet = int(args.sheet)
    skip = 1
    header = 0
    etype='FITBIT'
    print(("Input:", inputfile))
    if access(inputfile, R_OK):
        try:
            print(("Loading ", inputfile))
            dp = FitbitParser(inputfile, sheet, skip, header,etype)
            xsdtypes = dp.getxsd()
            print((dp.data.head()))
            for sd in dp.subjects:
                print(('\n***********SubjectID:', sd))
                for i, row in dp.subjects[sd].iterrows():
                    interval = int(row['interval'])
                    sampleid = dp.getSampleid(sd, interval)
                    print(('Sampleid:', sampleid))
                    (mandata, data) = dp.mapData(row, i)
                    print(mandata)
                    print(data)

        except Exception as e:
            print(("Error: ", e))

    else:
        print(("Cannot access file: ", inputfile))
