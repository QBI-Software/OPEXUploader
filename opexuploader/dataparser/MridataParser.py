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
import re
import pandas as pd
from opexuploader.dataparser.abstract.DataParser import DataParser, stripspaces


def extract_subj(string):
    subject = re.search("(\\d{4})+([A-z]{2})", string).group(0)
    interval = re.search("(?<=ses-).*", string).group(0)
    if interval == '01':
        interval = '0'

    return (subject, int(interval))
#
# extract_subj("sub-1001DS_ses-06")
#
#
# subject = re.search("(\\d{4})+([A-z]{2})","sub-1001DS_ses-01").group(0)
# re.search("(?<=ses-).*", "sub-1001DS_ses-01").group(0)
#
#
# inputdir = r"Q:\DATA\DATA ENTRY\XnatUploaded\sampledata\mridata"
#
# df = pd.read_excel(join(inputdir, "ASHS_xs_volumes.xlsx"))
# df[['Subject','interval']] = df['subjname'].apply(lambda s: extract_subj(s)).apply(pd.Series)
# sheet = 1
# skip = 0
# header = None
# f2 = join(inputdir, "ASHS_xs_volumes.xlsx")
# etype = 'MRI ASHS'
#
# MridataParser(f2, sheet, skip, header, etype).fields
#
# ['Subject', 'interval'] + MridataParser(f2, sheet, skip, header, etype).fields
VERBOSE = 0
class MridataParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        df = self.data
        df[['Subject', 'interval']] = df['subjname'].apply(lambda s: extract_subj(s)).apply(pd.Series)
        # cols = ['Subject', 'interval'] + self.fields

        self.data = df
        self.sortSubjects('Subject')
        if self.getPrefix() =='ASHS':
            self.data = self.normalizeICV()
        #sort subjects
        self.sortSubjects('Subject')


    def normalizeICV(self):
        """
        Normalize data with ICV data column per individ
        :param self:
        :return: dataframe
        """
        if self.data is not None and len(self.data) > 0:
            for blankcol in ['left_head', 'left_tail', 'right_head', 'right_tail']:
                if blankcol not in self.data.columns:
                    self.data.insert(0, blankcol, 0)
            cols = ['_CA1', '_CA2', '_DG', '_CA3', '_SUB']
            for lr in ['left', 'right']:
                lrcols = [lr + c for c in cols]
                self.data[lr + '_Hippoc'] = self.data.apply(lambda x: (x.loc[lrcols].sum()), axis=1)
            self.data['Total_Hippoc'] = self.data.apply(lambda x: (x.loc[['left_Hippoc', 'right_Hippoc']].sum()), axis=1)
            # Divide all values by ICV
            starti = 8
            endi = len(self.data.columns)
            df_ids = self.data[['Subject', 'Visit']]
            self.data = self.data.apply(lambda x: (x[starti:endi] / x.loc['icv']), axis=1)
            df = df_ids.join(self.data)
            # Save to new data file
            fname_calc = self.datafile.replace(self.ftype, '_ICV.xlsx')
            df.to_excel(fname_calc, sheet_name='ICV normalized', index=0)
            msg = 'ICV Normalized data: %s' % fname_calc
        else:
            msg = 'No data found'
        print(msg)
        #logging.info(msg)
        return df

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
        for ctab in self.fields:
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
    parser.add_argument('--filedir', action='store', help='Directory containing files', default="..\\sampledata\\mridata")

    args = parser.parse_args()
    inputdir = args.filedir
    print(("Input:", inputdir))
    if access(inputdir, R_OK):
        sheet = 1
        skip = 0
        header = None

        seriespattern = '*.xlsx' # originally .csv
        try:
            files = glob.glob(join(inputdir, seriespattern))
            print(("Files:", len(files)))
            for f2 in files:
                print(("Loading ", f2))
                etype = 'MRI'
                if 'ASHS' in f2:
                    etype += ' ASHS'
                elif 'FreeSurf' in f2:
                    etype += ' FS'
                else:
                    raise ValueError("Cannot determine MRI type")
                msg = "Running %s" % etype
                print(msg)
                dp = MridataParser(f2, sheet, skip, header, etype)

                for sd in dp.subjects:
                    for i, row in dp.subjects[sd].iterrows():
                        msg = '**SubjectID: %s Visit: %d' % ( sd, int(row['Visit']))
                        print(msg)
                        for ctab in dp.fields:
                            if ctab in row:
                                msg1 = "Field: %s = %d" % (ctab, row[ctab])
                                print(msg1)

        except Exception as e:
            print(("ERROR: ", e))
    else:
        print(("Cannot access directory: ", inputdir))
