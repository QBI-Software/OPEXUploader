# -*- coding: utf-8 -*-
"""
Utility script: CantabParser
Reads an excel or csv file with CANTAB data and extracts per subject
run from console/terminal with (example):
>python CantabParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
from datetime import datetime
from os import R_OK, access
from os.path import join

import pandas

from opexuploader.dataparser.abstract.DataParser import DataParser

VERBOSE = 0
class CantabParser(DataParser):

    def __init__(self, *args):
        DataParser.__init__(self, *args)
        try:
            # fields = join(self._DataParser__findResourcesdir(), 'cantab_fields.csv')
            # self.cantabfields = pandas.read_csv(fields, header=0)
            self.sortSubjects('Participant ID')
        except Exception as e:
            print(e)
            raise e



    def formatDateString(self,orig):
        '''Reformats datetime string from yyyy.mm.dd hh:mm:ss to yyyy-mm-dd'''
        dt = datetime.strptime(orig, "%Y.%m.%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")

    def getStringDateUTC(self, orig):
        '''Returns datetime string as a unique id'''
        dt = datetime.strptime(orig, "%Y.%m.%d %H:%M:%S UTC")
        return dt.strftime("%Y%m%d%H%M%S")

    def genders(self):
        return {0: 'male', 1: 'female'}

    def formatDob(self,orig):
        """
        Reformats DOB string from yyyy-mm-dd 00:00:00 as returned by series obj to yyyy-mm-dd
        """
        try:
            if "-" in orig:
                dt = datetime.strptime(orig,"%d-%b-%y") #if was 20-Oct-50
            elif "/" in orig:
                dt = datetime.strptime(orig, "%d/%m/%Y")
        except ValueError as e:
            dt = datetime.strptime(orig, "%Y-%m-%d %H:%M:%S")
        if dt is not None and dt.year > 2000:
            dt = datetime(dt.year-100, dt.month, dt.day)
        return dt.strftime("%Y-%m-%d")

    def getInterval(self,orig):
        """Parses string M-00 to 0 or M-01 to 1 etc"""
        interval = int(orig[2:])
        return interval

    def getSampleid(self, sd, row):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        cantabid = sd + '_' + self.getStringDateUTC(row['Visit Start (GMT)'])
        return cantabid


    def getxsd(self):
        xsd ={'MOT':'opex:cantabMOT',
            'PAL':'opex:cantabPAL',
            'SWM':'opex:cantabSWM',
            'ERT':'opex:cantabERT',
            'DMS':'opex:cantabDMS'
              }
        return xsd

    def getCommentstring(self):
        """
        Ensure comment string is exactly as appears in spreadsheet
        :return:
        """
        xsd = {'MOT': 'MOT Voice Comment',
               'PAL': 'PAL Recommended Standard Comment',
               'SWM': 'SWM Recommended standard Comment',
               'ERT': 'ERT Short Comment',
               'DMS': 'DMS Recommended Standard Comment'
               }
        return xsd

    def getStatusstring(self):
        """
                Ensure comment string is exactly as appears in spreadsheet
                :return:
                """
        xsd = {'MOT': 'MOT Voice Status',
               'PAL': 'PAL Recommended Standard Status',
               'SWM': 'SWM Recommended standard Status',
               'ERT': 'ERT Short Status',
               'DMS': 'DMS Recommended Standard Status'
               }
        return xsd

    def mapData(self, row,i, type):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """
        xsd = self.getxsd()[type]

        mandata = {
            xsd + '/interval': self.getInterval(row['Visit Identifier']),
            xsd + '/date': row['Visit Start (Local)'],  # PARSED in experiment load
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial',
            xsd + '/status': str(row[self.getStatusstring()[type]]),
            xsd + '/comments': str(row[self.getCommentstring()[type]])
        }
        motdata={}
        cantabfields = self.dbi.getFields('CANTAB ' + type)
        for ctab in cantabfields:
            motdata[xsd + '/' + ctab] = str(row[ctab])
        return (mandata, motdata)


    def getDFExpts(self,expts, interval, prefix=None):
        """
        Load expts as dataframe
        :param expts: collection of specific type of expt eg cantabMOT
        :param interval: which interval or * for all
        :param prefix: expt type prefix for getting fields
        :return: fully loaded valid data as dataframe
        """
        teste = expts.fetchone()
        xsd = teste.datatype()
        if prefix is None:
            prefix = [key for key,val in self.getxsd().iteritems() if val == xsd][0]

        ##Checking OK
        print(teste.get())
        print("DEBUG: Label=", teste.attrs.get('label'))
        print("DEBUG: Status=", teste.attrs.get(xsd +'/status'))
        ##Filter valid data
        df_expts = pandas.DataFrame([(e.attrs.get(xsd +'/interval'),
                                      e.attrs.get(xsd +'/data_valid'),
                                      e.attrs.get(xsd +'/sample_quality'), e) for e in expts],
                                    columns=['Interval', 'Valid', 'Quality', 'expt'])
        df = df_expts[(df_expts.Valid != "Invalid") & (df_expts.Quality != "Poor") & (df_expts.Interval == interval)]
        #generate columns with fields
        for field in self.cantabfields[prefix].dropna():
            fieldvals = []
            print("loading field=", field)
            for exp in df.expt:
                #print(exp.attrs.get(xsd + '/' + field.lower()))
                fieldvals.append(exp.attrs.get(xsd + '/' + field.lower()))
            df[field]=fieldvals
        #remove column with objects
        df.drop('expt', axis=1, inplace=True)
        #print(df)
        return df


    def getSubjectData(self,sd):
        """
        Load subject data from input data
        :param sd:
        :return:
        """
        skwargs = {}
        if self.subjects is not None:
            dob = self.formatDob(str(self.subjects[sd]['Date of Birth'].iloc[0]))
            gender = self.genders()[self.subjects[sd]['Gender'].iloc[0]]
            group = str(self.subjects[sd]['Group'].iloc[0])
            skwargs = {'dob': dob, 'gender': gender, 'group': group}
        return skwargs

########################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Parse CANTAB Files',
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files', default="..\\..\\sampledata\\cantab")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="RowBySession_HealthyBrains")

    args = parser.parse_args()

    inputdir = args.filedir
    sheet = args.sheet

    print("Input:", inputdir)
    if access(inputdir, R_OK):
        seriespattern = '*.csv'
        skip = 0
        header = None
        etype = 'CANTAB'
        try:
            files = glob.glob(join(inputdir, seriespattern))
            print("Files:", len(files))
            for f2 in files:
                print("Loading",f2)
                cantab = CantabParser(f2, sheet, skip, header, etype)
                #cantab.sortSubjects()
                print('Subject summary')
                for sd in cantab.subjects:
                    print('ID:', sd)
                    for i, row in cantab.subjects[sd].iterrows():
                        dob = cantab.formatDob(str(cantab.subjects[sd]['Date of Birth'][i]))
                        print(i, 'Visit:', row['Visit Identifier'], 'DOB', dob)
                        for ctab in cantab.fields:
                            print(ctab, row[ctab]) #'MOTML', row['MOTML'],'MOTSDL',row['MOTSDL'] )


        except ValueError as e:
            print("Sheet not found: ", e)

        except OSError as e:
            print("OS error:", e)

    else:
        print("Cannot access directory: ", inputdir)
