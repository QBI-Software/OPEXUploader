# -*- coding: utf-8 -*-
"""
Utility script: AcerParser
Reads an excel or csv file with data and extracts per subject
run from console/terminal with (example):
>python AcerParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
from os import R_OK, access
from os.path import join
import numpy as np
from opexuploader.dataparser.abstract.DataParser import DataParser

VERBOSE = 0


class AcerParser(DataParser):

    def __init__(self, *args):
        DataParser.__init__(self, *args)

        cols = ["AttentionOrientation", "Memory", "Fluency", "Language", "Visuospatial", "MMSE", "ACERTotal"]
        self.fields = ['attention', 'memory', 'fluency', 'language', 'visuospatial', 'MMSE', 'total']
        df = self.data
        df = df[['ID', 'TimePoint'] + cols]
        # df['ID'] = df['ID'].apply(lambda x: getID(x))
        df.columns=['ID', 'interval'] + self.fields
        self.data = df
        self.sortSubjects()

    def mapData(self, row, i, xsd=None):
        """
        Maps required fields from input rows
        :param row:
        :return:
        """
        interval = str(row['interval']) #NB There is no visit identifier
        if xsd is None:
            xsd = self.getxsd()
        mandata = {
            xsd + '/interval': str(interval),
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial'
        }
        motdata = {}
        for field in self.fields:
            if field in row and not np.isnan(row[field]):
                mandata[xsd + '/' + field] = "%0.f" % row[field]

        return (mandata,motdata)

    def getSubjectData(self,sd):
        """
        Extract subject data from input data
        :param sd:
        :return:
        """
        skwargs = {}
        if self.subjects is not None:
            dob = self.formatDobNumber(self.subjects[sd]['DOB'].iloc[0])
            gender = str(self.subjects[sd]['Sex'].iloc[0]).lower()
            skwargs = {'dob': dob}
            if gender in ['F', 'M']:
                skwargs['gender'] = gender

        return skwargs

    def getSampleid(self,sd, row):
        """
        Generate a unique id for data sample
        :param row:
        :return:
        """
        try:
            id = self.getPrefix() + "_" + sd + "_" + str(row['interval']) + 'M'
        except:
            raise ValueError('Cannot find Visit')
        return id

    def validData(self,dvalues):
        """
        Checks data is present in list
        -	-	-

        :param dvalues:
        :return:
        """
        rtn = True
        if isinstance(dvalues,list):
            for d in dvalues:
                if isinstance(d,str) or isinstance(d,str) or np.isnan(d):
                    rtn = False
                    break

        return rtn


########################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='ACE-R Files',
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')

    parser.add_argument('--filedir', action='store', help='Directory containing files', default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\acer")
    # parser.add_argument('--sheet', action='store', help='Sheet name to extract', default="0")
    args = parser.parse_args()

    inputdir = args.filedir
    # sheet = args.sheet
    skip=0
    header=None

    # # inputdir = r"Q:\DATA\DATA ENTRY\XnatUploaded\sampledata\acer"
    # skip, header, etype = (0, None, 'ACER')
    # inputdir ="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\acer"

    print(("Input:", inputdir))
    if access(inputdir, R_OK):
        seriespattern = '*.xlsx*'
        etype ='ACER'
        try:
            files = glob.glob(join(inputdir, seriespattern))
            print(("Files:", len(files)))
            for f2 in files:
                print(("Loading",f2))
                for sheet in range(0,2):
                    print(("Interval:", sheet))
                    dp = AcerParser(f2,sheet,skip,header,etype)
                    xsd = dp.getxsd()

                    print('Subject summary')
                    for sd in dp.subjects:
                        print(( '***Subject:', sd))
                        for i, row in dp.subjects[sd].iterrows():
                            print((dp.getSampleid(sd, row)))
                            (mandata,data) = dp.mapData(row,i,xsd)
                            print(mandata)
                            print(data)

                    #     dob = dp.subjects[sd]['DOB']
                    #     for i, row in dp.subjects[sd].iterrows():
                    #         print( dp.getSampleid(sd,row))
                    #         (mdata,data) = dp.mapData(row,i,xsd)
                    #         print( mdata )
                    #         print( data )



        except ValueError as e:
            print(("Sheet not found: ", e))

        except:
            raise OSError

    else:
        print(("Cannot access directory: ", inputdir))

