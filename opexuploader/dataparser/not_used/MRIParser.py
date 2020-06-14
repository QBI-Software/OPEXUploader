"""
@title:         MRI Parser
@author:        Alan Ho
@date:          2018-11-19
@last modified: 2018-11-23
@description:   Parses FMRI files into uploadable format

copyright (c) Alan Ho, 2018
"""

import pandas as pd
import numpy as np
import sys
import re
import os
import argparse
from openpyxl import load_workbook
import logging
from logging.handlers import RotatingFileHandler

from os import R_OK, access, listdir, mkdir, listdir
from os.path import join, expanduser, dirname, abspath, basename
from datetime import datetime

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser

ashslong_dict = {
    '0': 'clear label',
    '1': 'CA1',
    '2': 'CA2',
    '3': 'DG',
    '4': 'CA3',
    '7': 'misc',
    '8': 'SUB',
    '10': 'ERC',
    '11': 'BA35',
    '12': 'BA36',
    '13': 'PHC',
    '14': 'sulcus'
}

class MRIParser(DataParser):

    def __init__(self, inputdir, *args):
        DataParser.__init__(self, *args)

        self.inputdir = inputdir
        self.etype = basename(dirname(self.inputdir))
        self.interval = basename(inputdir)[0:-1]
        fields = ['CA1','CA2','DG','CA3','misc','SUB','ERC','BA35','BA36','PHC','sulcus', 'Hippoc']
        flist = [[side + '_' + f for f in fields] for side in ['left', 'right']]
        self.fields = ['icv'] + [item for sublist in flist for item in sublist] + ['Total_Hippoc']

        self.parse()
        self.sortSubjects('Subject')


    def parse(self):

        filelist = os.listdir(self.inputdir)

        print(len(filelist))

        datalist = {'vol': [], 'icv': []}
        empty_list = []
        for file in filelist:

            try:
                if 'icv' in file:

                    temp = process_icv(self.inputdir, file)
                    datalist['icv'].append(temp)




                else:
                    temp = process[self.etype](self.inputdir, file)
                    datalist['vol'].append(temp)




                msg = 'Success: {}'.format(file)
                print(msg)

            except:
                msg = 'Cannot process: {}'.format(file)
                print(msg)

                subject = re.findall('[0-9]{4}[A-Z]{2}', file)
                empty = pd.DataFrame({'Type': self.etype, 'Subject': subject, 'interval': self.interval, 'File': file})
                empty_list.append(empty)

        try:
            data = pd.concat(datalist['vol']). \
                pivot_table(values='volume', index='Subject', columns='region'). \
                reset_index()

            sum_cols = ['CA1', 'CA2', 'CA3', 'DG', 'SUB']
            for side in ['left', 'right']:
                data[side + '_Hippoc'] = data[[side + '_' + i for i in sum_cols]].sum(axis=1)

            data['Total_Hippoc'] = data['left_Hippoc'] + data['right_Hippoc']
            data['interval'] = int(self.interval)

            self.data = pd.merge(data.reset_index(), pd.concat(datalist['icv']).reset_index(), on='Subject')
            self.empty_data = pd.concat(empty_list)

        except:
            print(('problem with {}'.format(file)))

    def getSampleid(self, sd):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = self.etype.upper() + '_' + sd + '_' + str(self.interval)+'M'
        return id

    def getxsd(self):

        xsd = {
            'ashsraw': 'opex:ashsraw',
            'ashslong2': 'opex:ashslong2',
            'ashslong3': 'opex:ashslong3'
        }

        return xsd[self.etype]

    def mapData(self, row, xsd=None):

        if xsd is None:
            xsd = self.getxsd()

        mandata = {
            # xsd + '/date': str(self.date),
            xsd + '/interval': str(self.interval),
            xsd + '/sample_id': '',  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': ''
        }

        motdata = {}
        for ctab in self.fields:
            motdata[xsd + '/' + ctab] = str(row[ctab].iloc[0])
        return (mandata, motdata)



def process_icv(inputdir, file):
    linelist =[]

    with open(join(inputdir, file), 'r') as infile:
        for line in infile:
            subject = re.findall('(?<=sub-)([^\s]+)', line)[0]
            icv = re.findall('(?<=\s){2}.*', line)[0]
            df = pd.DataFrame({
                'Subject': subject,
                'icv': icv
            }, index=[0])
            linelist.append(df)

    data = pd.concat(linelist)
    data['icv'] = data['icv'].astype(float)

    return data

def process_raw(inputdir, file):
    columns = ['Subject', 'hemi', 'region', 'pixel', 'volume']

    df = pd.read_csv(join(inputdir, file), sep=' ', names=columns)
    df = df[df['region'] != 'clear label']
    df['Subject'] = df['Subject'].map(lambda x: re.findall('[0-9]{4}[A-Z]{2}', x)[0])
    df['region'] = df['hemi'] + '_' + df['region']

    return df[['Subject', 'region', 'volume']]

def process_long(inputdir, file):
    select_columns = ['Subject', 'region', 'volume']
    linelist = []
    subject = re.findall('[0-9]{4}[A-Z]{2}', file)[0]

    with open(join(inputdir, file), 'r') as infile:
        subject = re.findall('[0-9]{4}[A-Z]{2}', file)[0]
        hemisphere = re.findall('(?<=\_)(.*?)(?=_)', file)[0]

        for line in infile:
            result = re.split(' ', line)
            result = [x for x in result if x != '']
            if 'LabelID' in result:
                cut = result.index('Vol(mm^3)')

            linelist.append(result[0:(cut + 1)])

    df = pd.DataFrame(linelist[1:], columns=linelist[0])
    df['LabelID'].replace(ashslong_dict, inplace=True)
    df = df[df['LabelID']!='clear label']
    df['region'] = hemisphere + '_' + df['LabelID']
    df['volume'] = df['Vol(mm^3)'].astype(float)

    df['Subject'] = subject

    df = df[select_columns]
    return df

# process dictionary ------
process = {'ashsraw': process_raw, 'ashslong2': process_long, 'ashslong3': process_long}

##########################################
if __name__ == '__main__':
    """
    This script can read the raw txt files produced by ASHS to compute volumes and then directly uploads them to Xnat

    """

    parser = argparse.ArgumentParser(prog="MRIparser",
                                     description="""\
                                     Parses MRI txt files to extract volume data. Also looks for empty / nonprocessible files 
                                     """)
    parser.add_argument('--inputdir', action='store',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\mridatanew\\ashsraw")

    parser.add_argument('--saveempty', action='store',
                        default="n")

    parser.add_argument('--xnatformat', action='store',
                        default="n")

    args = parser.parse_args()

    rootdir = args.inputdir
    subdirs = os.listdir(rootdir)
    # etype = basename(rootdir)
    seriespattern = '.txt'
    save_empty = args.saveempty
    xnatformat = args.xnatformat


    for dir in subdirs:
        if dir not in ['0m', '6m', '12m']:
            continue

        interval = dir[0:-1]
        print(('Interval:', interval))
        inputdir = join(rootdir, dir)

        dp = MRIParser(inputdir)

        if save_empty == 'y':
            import openpyxl

            filename = basename(rootdir) + '.xlsx'
            path = join(os.getcwd(), filename)
            print('saving empty file list to {}'.format(path))
            writer = pd.ExcelWriter(path, engine='openpyxl')

            if os.path.exists(path):
                book = openpyxl.load_workbook(path)
                writer.book = book

            dp.empty_data.to_excel(writer, sheet_name=dir)
            writer.save()
            writer.close()

        if xnatformat == 'y':
            for sd in dp.subjects:
                row = dp.subjects[sd]
                (mandata, data) = dp.mapData(row)
                print(data)

    # msg = """***** MRI PARSER ****** \n Run on {} """.format(datetime.today())
    # logging.info(msg)
    # try:
    #     for inputdir in subdirs:
    #         if inputdir not in ['0m', '6m', '12m']:
    #             continue
    #         interval = inputdir[0:-1]
    #         print('Interval:', interval)
    #         inputdir = join(rootdir, inputdir)
    #         dp = MRIParser(inputdir)
    #         print(dp.data)
    #         print(dp.fields)
    #         for sd in dp.subjects:
    #             row = dp.subjects[sd]
    #             (mandata, data) = dp.mapData(row)
    #             print(data)
    #
    # except:
    #     pass