
# """
# Utility script: IpaqParser
# Reads an excel or csv file with data and extracts per subject
#
# Created 22/06/2018
#
# @author(s): Alan Ho and Liz Cooper-Williams, QBI
# """

import pandas as pd
import sys
import os
from os import R_OK, access
from os.path import join
import numpy as np
import argparse

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser,stripspaces


class IpaqParser(DataParser):
    def __init__(self, *args, **kwargs):
        DataParser.__init__(self, *args, **kwargs)
        if self.data is None:
            raise ValueError('IPAQ Parser: Data not loaded')
        self.type=''
        # if 'type' in kwargs:
        #     self.type = kwargs.get('type')
        #     self.fields = self.dbi.getFields(self.type)
        #     self.info = self.dbi.getInfo(self.type)
        # elif self.etype is not None:
        #     self.type = self.etype

        self.data.dropna(axis=1, how='all', inplace=True)
        # self.data = self.data.filter(regex="^[^78]")
        fields = ['sitting',
                  'walking_days',
                  'walking_time',
                  'moderate_days',
                  'moderate_time',
                  'vigorous_days',
                  'vigorous_time',
                  'pa',
                  'mvpa']
        self.fields = fields
        self.data = self.data[['ID'] + fields]
        # self.data.columns = ['ID'] + fields
        self.data['ID'] = self.data.apply(lambda x: stripspaces(x, 0), axis=1)
        # self.data['ID'] = self.data['ID'].apply(lambda x: getID(x))
        self.sortSubjects('ID')
        print('Data load complete')

        if self.info is None:
            self.info = {'prefix': 'IP', 'xsitype': 'opex:ipaq'}

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
        Map IPAQ data to row input data
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
        for field in self.fields:
            if field in row and not np.isnan(row[field].iloc[0]):
                mandata[xsd + '/' + field] = "%0.f" % row[field].iloc[0]
        return (mandata, motdata)

    def validData(self,dvalues):
        """
        Checks data is present in list
        -	-	-

        :param dvalues:
        :return:
        """
        rtn = True
        dvalues = dvalues[1:]
        if isinstance(dvalues,list):
            for d in dvalues:
                if isinstance(d,str) or isinstance(d,str):
                    rtn = False
                    break

        return rtn


###### RUN ###########
import sys
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
                Reads files in a directory and extracts data for upload to XNAT

                 ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="Q:\\WORKING DATA\\IPAQ\\3. Ready for XNAT")
    parser.add_argument('--datafile', action='store', help='Filename of original data',
                        default="IPAQ_20180913_XNATREADY.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputfile = join(args.filedir, args.datafile)
    sheet = int(args.sheet)
    sheet = 0
    skip = 2
    header = None
    etype = 'IPAQ'
    interval = 0
    print(("Input:", inputfile))
    if access(inputfile, R_OK):
        try:
            print(("Loading ", inputfile))
            dp = IpaqParser(inputfile, sheet, skip, header, etype)
            xsdtypes = dp.getxsd()
            for sd in dp.subjects:
                sampleid = dp.getSampleid(sd, interval)
                print(('Sampleid:', sampleid))
                row = dp.subjects[sd]
                print(row)
                if dp.validData(row.values.tolist()[0]):
                    (mandata, data) = dp.mapData(row, interval, xsdtypes)
                    print(mandata)
                    print(data)

                # print('\n***********SubjectID:', sd)
                # for i in intervals:
                #     print('Interval:', i)
                #     iheaders = [c + "_" + str(i) for c in dp.fields]
                #     sampleid = dp.getSampleid(sd, i)
                #     print('Sampleid:', sampleid)
                #     row = dp.subjects[sd]
                #     if not dp.validData(row[iheaders].values.tolist()[0]):
                #         print('empty data - skipping')
                #         continue
                #     (mandata, data) = dp.mapData(row[iheaders], i, xsdtypes)
                #     print(mandata)
                #     print(data)

        except Exception as e:
            print(("Error: ", e))

    else:
        print(("Cannot access file: ", inputfile))


