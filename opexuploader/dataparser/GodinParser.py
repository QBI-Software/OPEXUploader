# -*- coding: utf-8 -*-
"""
Utility script: GodinParser
Reads an excel or csv file with data and extracts per subject

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
from os import R_OK, access
from os.path import join

import numpy as np

from opexuploader.dataparser.abstract.DataParser import DataParser, stripspaces


class GodinParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        # cleanup subjects
        self.data['ID'] = self.data.apply(lambda x: stripspaces(x, 0), axis=1)
        # self.data['ID'] = self.data['ID'].apply(lambda x: getID(x))
        if self.info is None:
            self.info = {'prefix': 'GDN', 'xsitype': 'opex:godin'}
        # Replace field headers
        self.fields = ['strenuous','moderate','light','total', 'sweat']
        fields = ['strenuous','moderate','light','total', 'sweat']
        cols = ['ID', 'Strenuous', 'Moderate', 'Light', 'Totalleisureactivityscore', 'Sweat(1,2,or3)']
        ncols = ['SubjectID']
        renamecols = dict(list(zip(cols, ncols + fields)))

        df = self.data.iloc[:,0:7]
        df.dropna(axis=0, how='any', thresh=5, inplace=True)   # remove all empty rows
        df.fillna(999, inplace=True) # replace any remaining na with 999
        df.rename(columns= renamecols,
                  inplace=True)
        df.reindex()
        self.data = df
        # sort subjects
        self.sortSubjects('SubjectID')
        print('Data load complete')

    def getSampleid(self, sd, interval):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = self.getPrefix() + '_' + sd + '_' + str(interval) + 'M'
        return id

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
                if isinstance(d, str) or isinstance(d, str):
                    rtn = False
                    break

            if all([np.isnan(d) for d in dvalues]):
                rtn = False

        return rtn


########################################################################

if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\godin")
    parser.add_argument('--datafile', action='store', help='Filename of original data',
                        default="GODIN_20181220_FINAL_XR.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputfile = join(args.filedir, args.datafile)
    sheet = int(args.sheet)
    skip = 0 # 2 original
    header = None # 1 original
    etype = 'Godin'
    print(("Input:", inputfile))
    if access(inputfile, R_OK):
        try:
            print(("Loading ", inputfile))
            dp = GodinParser(inputfile, sheet, skip, header, etype)
            xsdtypes = dp.getxsd()

            intervals = list(range(0, 13, 3))
            for sd in dp.subjects:
                if '1044' in sd:
                    print(('\n***********SubjectID:', sd))
                    for i in intervals:
                        print(('Interval:', i))
                        iheaders = dp.fields
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
