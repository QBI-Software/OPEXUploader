"""

TITLE:  New MRI Parser

@author Alan Ho
"""

import glob
import os
import re
import sys
from os.path import join

import numpy as np

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser


class MriParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)

        df = self.data
        df['Subject'] = df['subjname'].apply(lambda x: re.findall('(?<=sub-)(.*)(?=_)', x)[0])
        df['interval'] = df['subjname'].apply(lambda x: int(re.findall('(?<=ses-)(.*)', x)[0]))
        renamecols = {
            'ICV':'icv',
            'right_subiculum': 'right_SUB',
            'left_subiculum': 'left_SUB'
        }
        df.rename(columns=renamecols, inplace=True)

        self.cols = [c for c in self.fields if c in df.columns]
        self.data = df[['Subject', 'interval'] + self.cols]
        self.sortSubjects('Subject')

    def getxsd(self):
        return 'opex:ashsraw'

    def getSampleid(self, sd, row):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'ASHSR_' + sd + '_' + str(row['interval'])+'M'
        return id

    def mapData(self, row, i):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """

        xsd = self.getxsd()

        mandata = {
            xsd + '/interval': str(row['interval']),
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial',
            xsd + '/comments': ""
        }
        motdata = {}
        for ctab in self.fields:
            if ctab in row and not np.isnan(row[ctab]):
                motdata[xsd + '/' + ctab] = str(row[ctab])

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


########################
if __name__ == '__main__':
    seriespattern = '*.xlsx'
    inputdir = 'Q:\DATA\DATA ENTRY\XnatUploaded\sampledata\mridata'

    sheet = 0
    skip = 0
    header = None
    etype = 'ASHSRaw'

    files = glob.glob(join(inputdir, seriespattern))

    print(("Files:", len(files)))
    for f2 in files:
        dp = MriParser(f2, sheet, skip, header, etype)
        # print(dp.data.head())
        # print(dp.subjects)

        iheaders = dp.cols

        for sd in dp.subjects:
            print(('\n***********SubjectID:', sd))
            for i, row in dp.subjects[sd].iterrows():
                sampleid = dp.getSampleid(sd, row)
                print(('Sampleid:', sampleid))
                if dp.validData(row[iheaders].values.tolist()):
                    (mandata, data) = dp.mapData(row, i)
                    print((mandata, data))
                else:
                    print('empty data - skipping')
                    continue


