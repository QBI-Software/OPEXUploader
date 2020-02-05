# -*- coding: utf-8 -*-
"""
Utility script: GodinParser
Reads an excel or csv file with data and extracts per subject

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
from os import R_OK, access, getcwd
from os.path import join

import numpy as np
import pandas as pd
import re
import sys

sys.path.append(getcwd())
# from DataParser import DataParser, stripspaces

from opexuploader.dataparser.abstract.DataParser import DataParser, stripspaces


class PacesParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        # cleanup subjects
        self.data['ID'] = self.data.apply(lambda x: stripspaces(x, 0), axis=1)
        # self.data['ID'] = self.data['ID'].apply(lambda x: getID(x))

        if self.info is None:
            self.info = {'prefix': 'GDN', 'xsitype': 'opex:paces'}
        # Replace field headers
        self.fields = ['q' + str(i) for i in range(1,9)] + ['total', 'enjoy_percent']
        columns = ['Q1','Q2','Q3','Q4', 'Q5', 'Q6', 'Q7', 'Q8','SumTotal','%Enjoyment']
        renamecols = dict(list(zip(columns, self.fields)))

        self.data.rename(columns= renamecols,
                         inplace=True)

        self.sortSubjects('ID')
        print('Data load complete')

    def getSampleid(self, sd, interval):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'PACES' + '_' + sd + '_' + str(interval) + 'M'
        return id

    def getxsd(self):
        return 'opex:paces'

    def mapData(self, row, i):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """

        xsd = self.getxsd()

        mandata = {
            xsd + '/interval': str(i),
            xsd + '/sample_id': str(row.index.values[0]),  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': ''
        }
        # One field in GODIN - is mandatory

        motdata = {}
        for field in self.fields:
            if field in row and not np.isnan(row[field].iloc[0]):
                mandata[xsd + '/' + field] = str(row[field].iloc[0])
        return (mandata, motdata)

    def validData(self, dvalues):
        """
        Checks data is present in list
        -	-	-

        :param dvalues:
        :return:
        """
        rtn = True
        if isinstance(dvalues, list):
            for d in dvalues:
                if isinstance(d, str) or isinstance(d, str) or np.isnan(d):
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
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\paces")
    parser.add_argument('--datafile', action='store', help='Filename of original data',
                        default="PACES_20181024_XR.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputfile = join(args.filedir, args.datafile)
    skip = 0 # 2 original
    header = None # 1 original
    etype = 'Paces'
    print(("Input:", inputfile))
    if access(inputfile, R_OK):
        try:
            print(("Loading ", inputfile))
            xl = pd.ExcelFile(inputfile)
            intervals = [int(re.findall('\\d{1,2}', s)[0]) for s in xl.sheet_names]
            for sheet in range(0, len(xl.sheet_names)):
                i = intervals[sheet]
                print(('Interval:', i))
                dp = PacesParser(inputfile, sheet, skip, header, etype)
                xsdtypes = dp.getxsd()
                iheaders = dp.fields
                for sd in dp.subjects:
                    sampleid = dp.getSampleid(sd, i)
                    row = dp.subjects[sd]
                    if iheaders[0] in row.columns:
                        print(('Sampleid:', sampleid))
                        if not dp.validData(row[iheaders].values.tolist()[0]):
                            print('empty data - skipping')
                            continue
                        (mandata, data) = dp.mapData(row[iheaders], i, xsdtypes)
                        print(mandata)
                        print(data)


        except Exception as e:
            print(("Error: ", e))

    else:
        print(("Cannot access file: ", inputfile))
