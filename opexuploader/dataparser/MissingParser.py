# -*- coding: utf-8 -*-
"""
Utility script: MissingParser


@author: Alan HO, QBI
"""

import argparse
import glob
from os.path import join

import pandas as pd

from opexuploader.dataparser.abstract.DataParser import DataParser


class MissingParser(DataParser):

    def __init__(self, **kwargs):
        # super(AmunetParser, self).__init__(*args) - PYTHON V3
        DataParser.__init__(self, **kwargs)
        self.data = missingData(self.datafile)

        self.sortSubjects('Subject')

    def getSampleid(self, sd, interval):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'MISSING' + '_' + str(sd) + '_' + str(interval) + 'M'
        return id

    def getxsd(self):
        return 'opex:missing'

    def mapData(self, row, i):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """
        xsd  = self.getxsd()

        mandata = {
            xsd + '/interval': str(i),
            xsd + '/comments': ''
        }

        motdata = {}
        for field in ['reason', 'experiment']:
            motdata[xsd + '/' + field] = str(row[field].iloc[0])
        return (mandata, motdata)


def missingData(filepath, type=None):
    wb = pd.read_excel(filepath, sheet=0)
    experiments = ['ACER', 'BPAQ', 'DASS', 'Godin', 'IPAQ', 'ISI', 'PACES', 'SF-36', 'Cosmed', 'hMWM Amunet 1',
                   'hMWM Amunet 2']
    cutpoints = wb.index[wb.iloc[:, 0].isin(experiments)]

    missingdata = []
    for i in range(len(cutpoints) - 1):
        slice = (cutpoints[i] + 1, cutpoints[i + 1] - 1)
        data = wb.iloc[slice[0]:slice[1], 0:3]. \
            rename(columns={'Missing Data Points for participants who have not dropped out': 'Subject',
                            'Unnamed: 1': 'interval',
                            'Unnamed: 2': 'reason'}). \
            dropna(). \
            assign(
            experiment=experiments[i],
            interval=lambda x: x.interval.str.extract(r'(\d*)').astype(int)
        )

        # data.columns = ['Subject', 'interval', 'reason']
        missingdata.append(data)

    if type is None:
        return pd.concat(missingdata)

    else:
        return pd.concat(missingdata).query('experiment == "{}"'.format(type))


###################################################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Parse Missing data',
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\missing")

    args = parser.parse_args()

    inputdir = args.filedir

    seriespattern = '*.xlsx'
    etype = 'MISS'
    files = glob.glob(join(inputdir, seriespattern))
    sheet = 0
    skip = 0

    for f2 in files:
        print(("Loading ", f2))
        dp = MissingParser(datafile=f2)
        xsdtypes = dp.getxsd()

        for sd in dp.subjects:
            print(('\n***********SubjectID:', sd))
            row = dp.subjects[sd]
            i = row['interval'].iloc[0]
            sampleid = dp.getSampleid(sd, i)
            print(('Sampleid:', sampleid))
            (mandata, data) = dp.mapData(row, i)
            print(data)