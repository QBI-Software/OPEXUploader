# -*- coding: utf-8 -*-
"""
Utility script: MridataParser
Reads an excel or csv file with MRI analysis data and extracts per subject
run from console/terminal with (example):
>python MridataParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
from datetime import datetime
from os import R_OK, access
from os.path import join

import pandas

from dataparser.DataParser import DataParser

VERBOSE = 0
class MridataParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        if 'ASHS' in self.datafile:
            self.type = 'ASHS'
        elif 'FreeSurf' in self.datafile:
            self.type = 'FS'
        else:
            raise ValueError("Cannot determine MRI type")
        try:
            fields = join(self.__findResourcesdir(), "MRI_fields.csv")
            access(fields, R_OK)
            df = pandas.read_csv(fields, header=0)
            self.cantabfields = df[self.type]
            self.cantabfields.dropna(how="all", axis=0, inplace=True)
            #Generate some fields from data file
            if self.data is not None and len(self.data)> 0:
                for blankcol in ['left_head','left_tail', 'right_head', 'right_tail']:
                    if blankcol not in self.data.columns:
                        self.data.insert(0,blankcol, 0)
                cols = ['_CA1','_CA2','_DG','_CA3','_SUB']
                for lr in ['left', 'right']:
                    lrcols = [lr + c for c in cols]
                    self.data[lr +'_Hippoc']= self.data.apply(lambda x: (x.loc[lrcols].sum()), axis=1)
                self.data['Total_Hippoc'] = self.data.apply(lambda x: (x.loc[['left_Hippoc','right_Hippoc']].sum()),axis=1)
                #Divide all values by ICV
                starti =8
                endi = len(self.data.columns)
                df_ids = self.data[['Subject','Visit']]
                self.data = self.data.apply(lambda x: (x[starti:endi]/x.loc['icv']), axis=1)
                df = df_ids.join(self.data)
                self.data = df
                #Save to new data file
                fname_calc = self.datafile.replace(self.ftype, '_ICV.xlsx')
                self.data.to_excel(fname_calc, sheet_name='ICV normalized',index=0)
                print('ICV Normalized data: ', fname_calc)
                #sort subjects
                self.sortSubjects('Subject')
        except:
            raise ValueError("Cannot access fields file")

    # def sortSubjects(self):
    #     '''Sort data into subjects by participant ID'''
    #     self.subjects = dict()
    #     if self.data is not None:
    #         ids = self.data['Subject'].unique()
    #         for sid in ids:
    #             sidkey = self._DataParser__checkSID(sid)
    #             self.subjects[sidkey] = self.data[self.data['Subject'] == sid]
    #             if VERBOSE:
    #                 print('Subject:', sid, 'with datasets=', len(self.subjects[sid]))
    #         print('Subjects loaded=', len(self.subjects))

    def formatDateString(self, orig):
        '''Reformats datetime string from yyyy.mm.dd hh:mm:ss to yyyy-mm-dd'''
        dt = datetime.strptime(orig, "%Y.%m.%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")

    def getStringDateUTC(self, orig):
        '''Returns datetime string as a unique id'''
        dt = datetime.strptime(orig, "%Y.%m.%d %H:%M:%S UTC")
        return dt.strftime("%Y%m%d%H%M%S")

    def genders(self):
        return {0: 'male', 1: 'female'}

    def formatDob(self, orig):
        """
        Reformats DOB string from yyyy-mm-dd 00:00:00 as returned by series obj to yyyy-mm-dd
        """
        # dt = datetime.strptime(orig,"%d-%b-%y") #if was 20-Oct-50
        # dt = datetime.strptime(orig, "%d/%m/%Y")
        dt = datetime.strptime(orig, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")

    def getInterval(self, orig):
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
        cantabid = sd + '_' + str(row['Visit'])
        return cantabid

    def getxsd(self):
        xsd = {'ASHS': 'opex:mriashs',
               'FS': 'opex:mrifs'
               }
        return xsd

    def mapData(self, row, i, xsd):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """

        mandata = {
            xsd + '/interval': str(row['Visit']),
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial',
            xsd + '/comments': ""
        }
        motdata = {}
        for ctab in self.cantabfields:
            if ctab in row:
                motdata[xsd + '/' + ctab] = str(row[ctab])
        return (mandata, motdata)

    def getSubjectData(self, sd):
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
    parser = argparse.ArgumentParser(prog='Parse MRI Analysis',
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files', default="sampledata\\mridata")
    parser.add_argument('--fields', action='store', help='MRI fields to extract',
                        default="..\\resources\\MRI_fields.csv")
    args = parser.parse_args()

    inputdir = args.filedir
    fields = args.fields
    print("Input:", inputdir)
    if access(inputdir, R_OK):
        seriespattern = '*.csv'
        try:
            files = glob.glob(join(inputdir, seriespattern))
            print("Files:", len(files))
            for f2 in files:
                print("Loading ", f2)
                cantab = MridataParser(fields, f2)
                #cantab.sortSubjects()
                for sd in cantab.subjects:
                    print('**SubjectID:', sd)
                    print("**MRI Fields**")
                    for i, row in cantab.subjects[sd].iterrows():
                        print(i, 'Visit:', row['Visit'])
                        for ctab in cantab.cantabfields:
                            if ctab in row:
                                print(ctab, "=", row[ctab])


        except ValueError as e:
            print("Sheet not found: ", e)

        except OSError as e:
            print("OS error:", e)

    else:
        print("Cannot access directory: ", inputdir)
