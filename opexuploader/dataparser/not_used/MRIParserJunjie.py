"""
@title:         MRI Parser
@author:        Alan Ho
@date:          2018-11-19
@last modified: 2018-11-23
@description:   Parses FMRI files into uploadable format

copyright (c) Alan Ho, 2018
"""

import argparse
import os
import re
import sys
from os.path import join

import pandas as pd

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser


class JunjieParser(DataParser):

    def __init__(self, inputdir, *args):
        DataParser.__init__(self, *args)

        self.inputdir = inputdir
        self.getData()
        self.sortSubjects('Subject')

    def getData(self):
        datalist = {}
        self.fields = []
        files = os.listdir(self.inputdir)
        for file in files:
            print(file)
            side = re.search('(right|left)', file).group(1)
            interval = re.search('(bl|m6|m12)', file).group(1)
            if interval == 'm12': interval = '12'
            if interval == 'm6': interval = '6'
            if interval == 'bl': interval = '0'

            data = pd.read_excel(join(self.inputdir, file))
            data['interval'] = interval
            sum_cols = ['CA1', 'CA2', 'CA3', 'DG', 'SUB']
            data['Hippoc'] = data[sum_cols].sum(axis=1)

            newfields = dict(list(zip(fields, [side + '_' + f for f in fields])))
            self.fields.append(list(newfields.values()))

            data.rename(columns=rename_dict, inplace=True)
            data.rename(columns=newfields, inplace=True)

            datalist[side + '_' + interval] = data.\
                                                reset_index().\
                                                rename(columns={'index': 'Subject', 'TIV': 'icv'})


        leftdf = pd.concat([datalist['left_0'], datalist['left_6'], datalist['left_12']])
        rightdf = pd.concat([datalist['right_0'], datalist['right_6'], datalist['right_12']])
        self.data = pd.merge(rightdf, leftdf, on=['Subject', 'interval', 'icv'], how='outer').\
                        assign(Total_Hippoc=lambda x: x.left_Hippoc + x.right_Hippoc,
                               icv=lambda x: x.icv * 1000
                               )
        self.fields = list(set(flatten(self.fields)))
        self.fields = self.fields + ['Total_Hippoc' , 'icv']

    def getxsd(self):
        return 'opex:mrijunjie'

    def getSampleid(self, sd, row):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'JUN' + '_' + sd + '_' + str(row['interval'])+'M'
        return id

    def mapData(self, row,i):
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
            xsd + '/status': '',
            xsd + '/comments': 'first run'
        }
        motdata={}
        for field in self.fields:
            motdata[xsd + '/' + field] = str(row[field])
        return (mandata, motdata)


flatten = lambda l: [item for fields in l for item in fields]

rename_dict = {
    'Whole_Hipp(mm*mm*mm)': 'Hippoc',
    'Whole Hipp(mm*mm*mm)': 'Hippoc',
    'TIV(cm*cm*cm)': 'icv'
}

fields = [
    'CA1',
    'CA2',
    'DG',
    'CA3',
    'SUB',
    'ERC',
    'BA35',
    'BA36',
    'PHC',
    'Hippoc'
]


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="MRIparser(Junjie)",
                                     description="""\
                                     Parses MRI data from Junjie's data
                                     """)
    parser.add_argument('--inputdir', action='store',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\mridata\\Junjie")
    parser.add_argument('--outputdir', action='store')



    args = parser.parse_args()

    inputdir = args.inputdir

    dp = JunjieParser(inputdir)

    print((dp.data))

    if args.outputdir is not None:
        dp.data.\
            set_index(['Subject', 'interval']).\
            to_csv(args.outputdir)

    # for sd in dp.subjects:
    #     print('*****SubjectID:', sd)
    #     for i, row in dp.subjects[sd].iterrows():
    #         sampleid = dp.getSampleid(sd, row)
    #         (mandata, data) = dp.mapData(row, i)
    #         print(mandata)
    #         print(data)