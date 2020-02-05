"""
@title:         FMRI Parser
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

import logging
from logging.handlers import RotatingFileHandler

from os import R_OK, access, listdir, mkdir, listdir
from os.path import join, expanduser, dirname, abspath, basename
from datetime import datetime

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser


#########################################

class FMRIParser(DataParser):

    def __init__(self, inputdir, fieldsfile='resources/fields/fmri.xlsx', *args):
        DataParser.__init__(self, *args)

        self.inputdir = inputdir
        self.fieldsfile = fieldsfile

        self.lookup()
        # self.fields = ['accProportions_Obj_5 ']
        self.getdata()
        self.sortSubjects('Subject')


    def lookup(self):
        lookup = \
            pd.read_excel(self.fieldsfile, index_col=0)[['XnatField']]. \
                to_dict(orient='index')

        for key in lookup:
            value = lookup[key]['XnatField']
            lookup[key] = value

        self.fields = list(lookup.values())
        print(self.fields)

        lookup['pptID'] = 'Subject'
        self.lookup = lookup


    def getdata(self):

        datalist = {'OverallSDT': [], 'OverallAccRT': []}
        for file in os.listdir(self.inputdir):

            type = re.split('_',file)[1]
            pattern = '(?<=\_)(\\d*?)(?=.csv)'
            interval = int(re.findall(pattern, file)[0])

            if interval == 1:
                interval = 0

            data = pd.read_csv(join(self.inputdir, file)).drop('ppt', axis=1)
            data_renamed = data.rename(columns=self.lookup)
            data_renamed['interval'] = interval

            datalist[type].append(data_renamed)

        SDT = pd.concat(datalist['OverallSDT'])
        ACC = pd.concat(datalist['OverallAccRT'])

        complete_data = pd.merge(SDT, ACC, on = ['Subject', 'interval'], how = 'outer')
        self.data = complete_data[['Subject', 'interval'] + self.fields]. \
                        sort_values(['Subject', 'interval'])


    def getxsd(self):
        return 'opex:fmri'

    def getSampleid(self, sd, row):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'FMRI_' + sd + '_' + str(row['interval'])
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
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Initial',
            xsd + '/comments': 'Alan Upload'
        }
        motdata={}

        for field in self.fields:
            motdata[xsd + '/' + field] = str(row[field])
        return (mandata, motdata)




def check_fmri(type, interval=0, subjects = ['1001DS', '1224CL']):
    data = dp.data[['Subject', 'interval'] + [type + '_' + str(i) for i in [3, 5]]].query('interval == {} & Subject in {}'.format(interval, subjects))
    return(data)


##########################################
if __name__ == '__main__':
    """
    This script can read the raw txt files produced by ASHS to compute volumes and then directly uploads them to Xnat

    """

    parser = argparse.ArgumentParser(prog="FMRIparser",
                                     description="""\
                                     Parses FMRI behavioural data files
                                     """)
    parser.add_argument('--inputdir', action='store',
                        default="Q:\\DATA\\7TMRIData\\behData\\behDataOutput\\fMRI_XNAT")

    args = parser.parse_args()

    inputdir = args.inputdir

    dp = FMRIParser(inputdir=inputdir)

    for sd in dp.subjects:
        print(('*****SubjectID:', sd))
        for i, row in dp.subjects[sd].iterrows():
            sampleid = dp.getSampleid(sd, row)
            print(sampleid)
            (mandata, data) = dp.mapData(row, i)
            print(mandata)
            print(data)





