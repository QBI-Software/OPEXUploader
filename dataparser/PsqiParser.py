# -*- coding: utf-8 -*-
"""
Utility script: PsqiParser
Reads an excel or csv file with data and extracts per subject

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
from os import R_OK, access
from os.path import join

import numpy as np

from dataparser.DataParser import DataParser, stripspaces


class PsqiParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        # Maybe empty sheet
        if self.data.empty or len(self.data.columns) <= 1:
            msg = "No data available"
            raise ValueError(msg)
        # cleanup subjects
        self.data['ID'] = self.data.apply(lambda x: stripspaces(x, 0), axis=1)
        if self.info is None:
            self.info = {'prefix': 'PSQ', 'xsitype': 'opex:psqi'}
        # Replace field headers
        self.fields = ['c'+str(i) for i in range(1,8)] # + ['total']
        ncols = ['SubjectID'] + self.fields
        cols = ['ID'] + [c for c in self.data.columns if (isinstance(c,unicode) or isinstance(c,str)) and c.startswith('Component')] # calculate total on upload + ['Global PQSI ']
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
        motdata = {}
        totalcols = 0
        for field in self.fields:
            if field in row and not np.isnan(row[field].iloc[0]):
                motdata[xsd + '/' + field] = str(row[field].iloc[0])
                totalcols += row[field].iloc[0]
        motdata[xsd + '/total'] = str(totalcols)
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
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\psqi")
    parser.add_argument('--datafile', action='store', help='Filename of original data',
                        default="PSQI data entry 20180206.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputfile = join(args.filedir, args.datafile)
    sheet = int(args.sheet)
    skip = 1
    header = 1
    etype = 'PSQI'
    print("Input:", inputfile)
    if access(inputfile, R_OK):
        try:
            print("Loading ", inputfile)
            intervals = range(0, 10, 3)
            for sheet in range(0, 4):
                i = intervals[sheet]
                print('Interval:', i)
                try:
                    dp = PsqiParser(inputfile, sheet, skip, header, etype)
                except ValueError as e:
                    print(e.args[0])
                    continue
                xsdtypes = dp.getxsd()

                for sd in dp.subjects:
                    print('\n***********SubjectID:', sd)
                    sampleid = dp.getSampleid(sd, i)

                    row = dp.subjects[sd]
                    if not dp.validData(row[dp.fields].values.tolist()[0]):
                        #print('empty data - skipping')
                        continue
                    print('Sampleid:', sampleid)
                    (mandata, data) = dp.mapData(row, i, xsdtypes)
                    print(mandata)
                    print(data)
            print("Complete")
        except Exception as e:
            print("Error: ", e)


    else:
        print("Cannot access file: ", inputfile)
