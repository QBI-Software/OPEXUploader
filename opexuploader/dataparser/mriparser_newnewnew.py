"""
@title:         MRI Parser
@author:        Alan Ho
@date:          2018-11-19
@last modified: 2018-11-23
@description:   Parses MRI data from the raw txt files into Xnat uploadable format

copyright (c) Alan Ho, 2018
"""

import pandas as pd
import numpy as np
import sys
import re
import os
import argparse

import logging
from logging.handlers import RotatingFileHandler

from os import R_OK, access, listdir, mkdir, listdir
from os.path import join, expanduser,dirname,abspath, basename
from datetime import datetime

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser

### Global config for logging required due to redirection of stdout to console in app
# logfile=join(expanduser('~'),'logs',',mriparser.log')
# if logfile is not None:
#     logbase = dirname(abspath(logfile))
#     if not access(logbase, R_OK):
#         mkdir(logbase)
#
# logging.basicConfig(filename=logfile,level=logging.DEBUG, format='%(asctime)s [%(filename)s %(lineno)d] %(message)s',
#                                 datefmt='%d-%m-%Y %I:%M:%S %p')
#
# logger = logging.getLogger('opex')
# handler = RotatingFileHandler(filename=logfile, maxBytes=4000000000)
# logger.addHandler(handler)



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

home = r'Q:\DATA\DATA ENTRY\XnatUploaded\sampledata\mridatanew\ashslong2\0m'

f = open(join(home, 'sub-1001DS_left_nogray_vols_01.txt'))

for line in f.readlines():
    print(line)

data = pd.read_csv(join(home, 'sub-1001DS_left_nogray_vols_01.txt'), sep='\s+', header=0, index_col=None)
data['LabelID'].map(ashslong_dict)

data[['LabelID','Vol(mm^3)']]

inputdir = home
filename = 'sub-1001DS_right_nogray_vols_01.txt'


pattern =  '(?<=\_)(.*?)(?=_)'
re.findall(pattern, filename)[0]



def get_data():

    # winner!!!!!!
    datalist = []
    with open(join(inputdir, filename), 'r') as infile:

        subject = re.findall('[0-9]{4}[A-Z]{2}', filename)[0]
        hemisphere = re.findall('(?<=\_)(.*?)(?=_)', filename)[0]

        for line in infile:
            result = re.split(' ', line)
            result = [x for x in result if x!='']
            if 'LabelID' in result:
                cut = result.index('Vol(mm^3)')

            datalist.append(result[0:(cut+1)])

    data = pd.DataFrame(datalist[1:],  columns=datalist[0])
    data['LabelID'].replace(ashslong_dict, inplace=True)
    data['LabelID'] = hemisphere + '_' + data['LabelID']
    data[['LabelID', ]]


    icvlist, datalist = [], []
    for file in os.listdir(self.inputdir):

        try:
            df_dict = parse_vol(self.inputdir, file)
            if 'data' in df_dict.keys():
                datalist.append(df_dict['data'])
            else:
                icvlist.append(df_dict['icv'])
            msg = 'SUCCESS: {}'.format(file)

        except ValueError as e:
            msg = "Error: {}".format(e)

        logging.info(msg)
        print(msg)




class MriParser:

    def __init__(self, inputdir):
        DataParser.__init__(self)

        self.inputdir = inputdir
        self.interval = basename(inputdir)[0:-1]
        self.etype = etype
        self.parse()

        fields = ['CA1','CA2','DG','CA3','misc','SUB','ERC','BA35','BA36','PHC','sulcus', 'Hippoc']
        flist = [[side + '_' + f for f in fields] for side in ['left', 'right']]
        self.fields = ['icv'] + [item for sublist in flist for item in sublist] + ['Total_Hippoc']
        self.sortSubjects('Subject')

    def parse(self):
        icvlist, datalist = [], []
        for file in os.listdir(self.inputdir):

            try:
                df_dict = parse_vol(self.inputdir, file)
                if 'data' in df_dict.keys():
                    datalist.append(df_dict['data'])
                else:
                    icvlist.append(df_dict['icv'])
                msg = 'SUCCESS: {}'.format(file)

            except ValueError as e:
                msg = "Error: {}".format(e)

            logging.info(msg)
            print(msg)

        data = pd.concat(datalist)
        data = data.pivot_table(values='volume', index='Subject', columns='region')

        sum_cols = ['CA1', 'CA2', 'CA3', 'DG', 'SUB']
        for side in ['left', 'right']:
            data[side + '_Hippoc'] = data[[side + '_' + i for i in sum_cols]].sum(axis=1)

        data['Total_Hippoc'] = data['left_Hippoc'] + data['right_Hippoc']
        data = pd.merge(data.reset_index(), pd.concat(icvlist).reset_index(), on='Subject')

        self.data = data


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

    def mapData(self, row):

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


def parse_vol(inputdir, filename):

    datalist = []

    with open(join(inputdir, filename), 'r') as infile:
        for line in infile:
            try:
                subject = re.findall('(?<=sub-)([^\s]+)', line)[0]

                if 'icv' in filename:
                    icv = re.findall('(?<=\s){2}.*', line)[0]
                    df = pd.DataFrame({
                        'Subject': subject,
                        'icv': icv
                    }, index=[0])
                    datalist.append(df)
                    data = pd.concat(datalist)

                else:
                    region = '_'.join(re.split('\s', line)[1:3])
                    pixel, volume = re.findall('(?<=\s){2}\d+\.?\d*', line)
                    df = pd.DataFrame({
                        'Subject': subject,
                        'region': region,
                        'pixel': float(pixel),
                        'volume': float(volume)
                    },
                        index=[0])

                    datalist.append(df)
                    data = pd.concat(datalist)

            except:
                pass

        tag = 'icv' if 'icv' in filename else 'data'

        return {tag: data}







##########################################
if __name__ == '__main__':
    """
    This script can read the raw txt files produced by ASHS to compute volumes and then directly uploads them to Xnat
    
    """

    parser = argparse.ArgumentParser(prog="MRIparser",
                                     description="""\
                                     Parses MRI txt files to extract volume data
                                     """)
    parser.add_argument('--inputdir', action='store',
                        default="Q:\\DATA\\7TMRIData\\test_run_upload\\ashsraw")

    args = parser.parse_args()

    rootdir = args.inputdir
    subdirs = os.listdir(rootdir)
    etype = basename(rootdir)
    seriespattern = '.txt'

    msg = """***** MRI PARSER ****** \n Run on {} """.format(datetime.today())
    logging.info(msg)
    try:
        for inputdir in subdirs:
            if inputdir not in ['0m', '6m', '12m']:
                continue
            interval = inputdir[0:-1]
            print('Interval:', interval)
            inputdir = join(rootdir, inputdir)
            dp = MriParser(inputdir, etype=etype)
            print(dp.fields)
            for sd in dp.subjects:
                row = dp.subjects[sd]
                (mandata, data) = dp.mapData(row)
                print(data)


    # try:
    #     dp = MriParser(inputdir, etype='ashsraw')
    #     # print(dp.data.head())
    #     print(dp.getxsd())
    #     # for sd in dp.subjects:
    #     #     sampleid = dp.getSampleid(sd)
    #     #     print('SampleID: ' + sampleid)
    #     #     mandata, data = dp.mapData(sd, 'ashslong2')
    #     #     print(mandata)
    #     #     print(data)


    except IOError as e:
        msg = 'ERROR:' + str(e)
        logging.error(msg)
        print(msg)

    except ValueError as e:
        msg = 'ValueError:' + str(e)
        logging.error(msg)
        print(msg)

    except Exception as e:
        msg = 'Exception:' + str(e)
        logging.error(msg)
        print(msg)




