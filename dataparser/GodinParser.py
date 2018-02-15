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

from dataparser.DataParser import DataParser, stripspaces


class GodinParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        # cleanup subjects
        self.data['ID'] = self.data.apply(lambda x: stripspaces(x, 0), axis=1)
        if self.info is None:
            self.info = {'prefix': 'GDN', 'xsitype': 'opex:godin'}
        # Replace field headers
        self.fields = ['total']
        ncols = ['SubjectID']
        for ix in range(0, 10, 3):
            ncols += [c + '_' + str(ix) for c in self.fields]
        cols = ['ID'] + [c for c in self.data.columns if c.startswith('Total')]
        df = self.data[cols]
        df.columns = ncols
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
            rfield = field + '_' + str(i)
            if rfield in row and not np.isnan(row[rfield].iloc[0]):
                mandata[xsd + '/' + field] = str(row[rfield].iloc[0])
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
                if isinstance(d, str) or isinstance(d, unicode) or np.isnan(d):
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
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\godin")
    parser.add_argument('--datafile', action='store', help='Filename of original data',
                        default="GODIN_Data_entry_180717.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputfile = join(args.filedir, args.datafile)
    sheet = int(args.sheet)
    skip = 2
    header = 1
    etype = 'Godin'
    print("Input:", inputfile)
    if access(inputfile, R_OK):
        try:
            print("Loading ", inputfile)
            dp = GodinParser(inputfile, sheet, skip, header, etype)
            xsdtypes = dp.getxsd()
            intervals = range(0, 13, 3)
            for sd in dp.subjects:
                print('\n***********SubjectID:', sd)
                for i in intervals:
                    print('Interval:', i)
                    iheaders = [c + "_" + str(i) for c in dp.fields]
                    sampleid = dp.getSampleid(sd, i)
                    row = dp.subjects[sd]
                    if iheaders[0] in row.columns:
                        print('Sampleid:', sampleid)
                        if not dp.validData(row[iheaders].values.tolist()[0]):
                            print('empty data - skipping')
                            continue
                        (mandata, data) = dp.mapData(row[iheaders], i, xsdtypes)
                        print(mandata)
                        print(data)

        except Exception as e:
            print("Error: ", e)

    else:
        print("Cannot access file: ", inputfile)
