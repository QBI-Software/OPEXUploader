
"""
TITLE  - Accelerometry Parser
@author Alan Ho, QBI 2018
"""
from __future__ import print_function
import sys

import os
import sys
import pandas as pd
import numpy as np
import glob
import argparse


from opexuploader.dataparser.abstract.DataParser import DataParser
from os.path import join, dirname, basename

class AccelParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)

        path = r'resources\fields'
        fields = pd.read_csv(join(path, 'accel_fields.csv'))['ACCELEROMETRY'].values.tolist()

        self.type = basename(dirname(self.datafile))
        self.location = basename(dirname(dirname(self.datafile)))
        print(self.location)
        if self.type == 'month':
            fields = [f for f in fields if f not in ['day', 'valid_day']]

        self.fields = fields
        self.data = self.data[['Subject', 'interval'] + self.fields]
        self.sortSubjects(subjectfield='Subject')

    def getSampleid(self, sd, row):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """

        if self.type == 'month':
            id = {
                'NCS': 'ACCM' + '_' + sd + '_' + str(row['interval']) + 'M',
                'custom': 'ACCMA' + '_' + sd + '_' + str(row['interval']) + 'M'
            }

        elif self.type == 'day':
            id = {
                'NCS': 'ACCD_{}_{}M_{}D_{}VD'.format(sd, row['interval'], row['day'], row['valid_day']),
                'custom': 'ACCDA_{}_{}M_{}D_{}VD'.format(sd, row['interval'], row['day'], row['valid_day'])
            }

            # 'ACCDA' + '_' + sd + '_' + str(row['interval']) + 'M' + '_' + str(row['day']) + 'D'

        return id[self.location]

    def getxsd(self):
        upload_dir = {
            'NCS': 'opex:accel' + self.type,
            'custom': 'opex:accel' + self.type + 'alt'
        }

        return upload_dir[self.location]


    def mapData(self, i, row):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """

        xsd = self.getxsd()

        mandata = {
            xsd + '/interval': str(row['interval']),
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': ''
        }
        motdata = {}
        for i in range(len(self.fields)):
            field = self.fields[i]
            if field in row and not np.isnan(row[field]):
                motdata[xsd + '/' + field] = str(row[field])
        return (mandata, motdata)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\accel\\NCS\\month")
    args = parser.parse_args()

    # inputdir = r'Q:\DATA\DATA ENTRY\XnatUploaded\sampledata\accel\day'
    inputdir = args.filedir
    seriespattern = '*.csv'
    sheet = 0
    skip = 0
    header = None
    etype = 'ACC'

    files = glob.glob(join(inputdir, seriespattern))

    for f2 in files:
        dp = AccelParser(f2, sheet,skip, header, etype)

        for sd in dp.subjects:
            print('\n***********SubjectID:', sd)
            for i, row in dp.subjects[sd].iterrows():
                sampleid = dp.getSampleid(sd,row)
                print('Sampleid:', sampleid)
                (mandata, data) = dp.mapData(i, row)
                print(mandata)
                print(data)
