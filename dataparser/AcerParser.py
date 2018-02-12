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

from dataparser.DataParser import DataParser

VERBOSE = 0
class AcerParser(DataParser):

    def __init__(self, *args):
        DataParser.__init__(self, *args)
        self.sortSubjects()


    def mapData(self, row, i, xsd=None):
        """
        Maps required fields from input rows
        :param row:
        :return:
        """
        interval = str(row['Visit']) #NB There is no visit identifier
        if xsd is None:
            xsd = self.getxsd()
        mandata = {
            xsd + '/interval': str(interval),
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial',
            xsd + '/attention': str(row['Attention and Orientation']),
            xsd + '/memory': str(row['Memory']),
            xsd + '/fluency': str(row['Fluency']),
            xsd + '/language': str(row['Language']),
            xsd + '/visuospatial': str(row['Visuospatial']),
            xsd + '/MMSE': str(row['MMSE Total']),
            xsd + '/total': str(row['ACE-R Total'])
        }

        data = {}
        return (mandata,data)


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
            id = self.getPrefix() + "_" + sd + "_" + str(row['Visit'])
        except:
            raise ValueError('Cannot find Visit')
        return id


########################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='ACE-R Files',
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')

    parser.add_argument('--filedir', action='store', help='Directory containing files', default="..\\sampledata\\acer")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract', default="1")
    args = parser.parse_args()

    inputdir = args.filedir
    sheet = args.sheet
    skip=0
    header=None
    print("Input:", inputdir)
    if access(inputdir, R_OK):
        seriespattern = '*.*'
        etype ='ACER'
        try:
            files = glob.glob(join(inputdir, seriespattern))
            print("Files:", len(files))
            for f2 in files:
                print("Loading",f2)
                dp = AcerParser(f2,sheet,skip,header,etype)
                xsd = dp.getxsd()
                print('Subject summary')
                for sd in dp.subjects:
                    print '***Subject:', sd
                    dob = dp.subjects[sd]['DOB']
                    for i, row in dp.subjects[sd].iterrows():
                        print dp.getSampleid(sd,row)
                        (mdata,data) = dp.mapData(row,i,xsd)
                        print mdata
                        print data


        except ValueError as e:
            print("Sheet not found: ", e)

        except:
            raise OSError

    else:
        print("Cannot access directory: ", inputdir)
