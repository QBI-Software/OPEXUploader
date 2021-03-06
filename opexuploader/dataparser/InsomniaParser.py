# -*- coding: utf-8 -*-
"""
Utility script: InsomniaParser
Reads an excel or csv file with data and extracts per subject

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
from os import R_OK, access
from os.path import join

import numpy as np

from opexuploader.dataparser.abstract.DataParser import DataParser, stripspaces


class InsomniaParser(DataParser):
    def __init__(self, *args,**kwargs):
        DataParser.__init__(self, *args)
        #Maybe empty sheet
        if self.data.empty or len(self.data.columns) <=1:
            msg ="No data available"
            raise ValueError(msg)
        # cleanup subjects
        self.data['ID'] = self.data.apply(lambda x: stripspaces(x, 0), axis=1)

        if self.info is None:
            self.info = {'prefix': 'INS', 'xsitype': 'opex:insomnia'}
        # Replace field headers
        self.fieldmap = {'q1': 'Q1',
                         'q2': 'Q2',
                         'q3': 'Q3',
                         'q4': 'Q4',
                         'q5': 'Q5',
                         'q6': 'Q6',
                         'q7': 'Q7',
                         'total': 'TotalScore'}
        cols = ['ID',
                self.fieldmap['q1'],
                self.fieldmap['q2'],
                self.fieldmap['q3'],
                self.fieldmap['q4'],
                self.fieldmap['q5'],
                self.fieldmap['q6'],
                self.fieldmap['q7'],
                self.fieldmap['total']]
        # self.fieldmap = {'total': 'TotalScore'}
        self.fields = list(self.fieldmap.keys())
        ncols = ['SubjectID'] + self.fields
        # cols = ['ID', self.fieldmap['total']]
        # zeros have been entered when should be blank
        self.data[self.fieldmap['total']] = self.data.apply(lambda x: self.nodatarow(x,self.fieldmap['total']), axis=1)
        self.data[cols[1:]] = self.data.apply(lambda x: self.nodatarow(x, cols[1:]), axis=1)
        df = self.data[cols]
        df = df.astype(object) # convert to object
        df.columns = ncols
        df.reindex()

        self.data = df
        # sort subjects
        self.sortSubjects('SubjectID')
        print('Data load complete')


    def nodatarow(self,row,fieldname):
        rtn = row[fieldname]
        if np.isnan(row[1]):
            rtn = ''
        return rtn

    def getSampleid(self, sd, interval):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id1
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
        #all data is mandata
        motdata = {}
        for field in self.fields:
            if field in row:
                row.replace('nan', '', inplace=True)
                mandata[xsd + '/' + field] = "%0.f" % row[field].iloc[0]
                mandata[xsd + '/' + field] = mandata[xsd + '/' + field].replace('nan', '')
        # for field in self.fields:
        #     if field in row and not np.isnan(row[field].iloc[0]):
        #         mandata[xsd + '/' + field] = "%0.f" % row[field].iloc[0]
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
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\isi")
    parser.add_argument('--datafile', action='store', help='Filename of original data',
                        default="ISI_20181220_XR.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputfile = join(args.filedir, args.datafile)
    #Data file has one sheet per interval
    skip = 0
    header = None
    etype = 'Insomnia'
    print(("Input:", inputfile))
    if access(inputfile, R_OK):
        try:
            print(("Loading ", inputfile))
            intervals = list(range(0, 13, 3))
            for sheet in range(0,5):
                i = intervals[sheet]
                print(('Interval:', i))
                dp = InsomniaParser(inputfile, sheet, skip, header, etype)
                if dp is None:
                    continue
                else:
                    dp.interval = i
                xsdtypes = dp.getxsd()
                for sd in dp.subjects:
                    print(('\n***********SubjectID:', sd))
                    sampleid = dp.getSampleid(sd, i)
                    print(('Sampleid:', sampleid))
                    row = dp.subjects[sd]
                    if not dp.validData(row[dp.fields].values.tolist()[0]):
                        print('empty data - skipping')
                        continue
                    (mandata, data) = dp.mapData(row, i, xsdtypes)
                    print(mandata)
                    print(data)

        except Exception as e:
            print(("Error: ", e))

    else:
        print(("Cannot access file: ", inputfile))
