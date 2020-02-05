
# """
# Utility script: BpaqParser
# Reads an excel or csv file with data and extracts per subject
#
# Created 22/06/2018
#
# @author(s): Alan Ho and Liz Cooper-Williams, QBI
# """

import argparse
import glob
import os
import sys
from os.path import join

import numpy as np

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser,stripspaces

# -------------------------------
class BpaqParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        # cleanup subjects
        self.data['ID'] = self.data.apply(lambda x: stripspaces(x, 0), axis=1)
        # self.data['ID'] = self.data['ID'].apply(lambda x: getID(x))
        df = self.data

        # Replace field headers
        self.fields = ['current', 'past', 'total']
        columns = ['CurrentResult', 'PastResult', 'TotalResult']
        df.rename(columns=dict(list(zip(columns, self.fields))), inplace=True)
        self.data = df
        self.sortSubjects('ID')
        print('Data load complete')

    def getSampleid(self, sd, interval):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'BPAQ' + '_' + str(sd) + '_' + str(interval) + 'M'
        return id

    def getxsd(self):
        return 'opex:bpaqscale'

    def mapData(self, row, i):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """
        xsd  = self.getxsd()

        mandata = {
            xsd + '/interval': str(i),
            xsd + '/sample_id': str(row.index.values[0]),  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': ''
        }

        motdata = {}
        for field in self.fields:
            if not np.isnan(row[field].iloc[0]):
                motdata[xsd + '/' + field] = str(row[field].iloc[0])
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

########################################################################################
if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\bpaq")
    parser.add_argument('--datafile', action='store', help='Filename of original data',
                        default="BPAQ_20180615_XR.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputdir = args.filedir
    sheet = int(args.sheet)
    skip = 0 # 2 original
    header = 0 # 1 original
    seriespattern = '*.xlsx'
    etype = 'BPAQ'
    files = glob.glob(join(inputdir, seriespattern))


    try:
        for f2 in files:
            print(("Loading ", f2))
            dp = BpaqParser(f2, sheet, skip, header, etype)
            xsdtypes = dp.getxsd()

            for sd in dp.subjects:
                print(('\n***********SubjectID:', sd))
                row = dp.subjects[sd]
                i = row['TimePoint'].iloc[0]
                sampleid = dp.getSampleid(sd, i)
                print(('Sampleid:', sampleid))
                (mandata, data) = dp.mapData(row, i)
                print(data)


    except Exception as e:
        print(("Error: ", e))

