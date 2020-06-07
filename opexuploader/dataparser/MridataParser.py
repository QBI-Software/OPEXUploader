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
from os import R_OK, access, path
import logging
import pandas as pd

from opexuploader.dataparser.abstract.DataParser import DataParser

VERBOSE = 0

class MridataParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)

        # Replace column name Visit with interval if exists
        if 'Visit' in self.data.columns:
            self.data.rename(columns={'Visit': 'interval'}, inplace=True)
        # remove any spaces in 'interval' and 'version' column names
        self.data.rename(columns={'version ': 'version', 'interval ': 'interval'}, inplace=True)

        if self.getPrefix() == 'ASHS':
            self.data = self.normalizeICV()
        elif self.getPrefix() == 'FMRI':
            # check if column headers need mapping to XNAT fields
            if self.fields[0] not in self.data.columns:
                df_fieldmap = pd.read_csv(path.join(self.resource_dir, 'fields', 'MRI_fields.csv'))
                if df_fieldmap.FMRImap[0] in self.data.columns:
                    cols = dict(zip(df_fieldmap.FMRImap, df_fieldmap.FMRI))
                    self.data.rename(columns=cols, inplace=True)
                else:
                    msg = 'FMRI fields do not correspond to XNAT fields or FMRImap fields in MRI_fields.csv - exiting'
                    raise ValueError(msg)

        # Sort rows into subjects
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
            self.data['Total_Hippoc'] = self.data.apply(lambda x: (x.loc[['left_Hippoc', 'right_Hippoc']].sum()),
                                                        axis=1)
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
        logging.info(msg)
        return df

    def formatDateString(self, orig):
        """
        Reformats datetime string from yyyy.mm.dd hh:mm:ss to yyyy-mm-dd
        """
        dt = datetime.strptime(orig, "%Y.%m.%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")

    def getStringDateUTC(self, orig):
        """
        Returns datetime string as a unique id
        """
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
        """
        Parses string M-00 to 0 or M-01 to 1 etc
        """
        interval = int(orig[2:])
        return interval

    def getSampleid(self, sd, row):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        sampleid = self.getPrefix() + '_' + sd + '_' + str(row['interval'])
        if self.etype == 'TASKRET' or self.etype == 'TASKENCODE':
            sampleid += 'M%s%s' % (str(row['condition']), str(row['load']))
        if hasattr(row, 'version') and len(row['version']) > 0:
            sampleid += '_' + str(row['version'])
        return sampleid

    def getxsd(self):
        """
        Get dict of opex namespaces
        :return:
        """
        xsd = {'ASHS': 'opex:mriashs',
               'FS': 'opex:mrifs',
               'FMRI': 'opex:fmri',
               'TASKRET': 'opex:fmritaskret',
               'TASKENCODE': 'opex:fmritaskencode'
               }
        return xsd

    def mapData(self, row, i, xsd):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """
        if hasattr(row, 'version'):
            version = 'Version %s' % str(row['version'])
            sample_id = '%s_%s' % (str(i), str(row['version']))
        else:
            version = ''
            sample_id = str(i)
        mandata = {
            xsd + '/interval': str(row['interval']),
            xsd + '/sample_id': sample_id,  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Initial',
            xsd + '/comments': version
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
            Reads files in a directory and extracts data for upload to XNAT for the following:
                  1. MRI analysis data - ASHS
                  2. MRI analysis data - FreeSurfer
                  3. MRI analysis data - fMRI behaviour
                  4. MRI analysis data - fMRI TaskRet
                  
            Fields for each type are shown in MRI_fields.csv.  These need to be present in the upload file.
            Include columns for 'SUBJECT, INTERVAL, VERSION' 
            Example data: '1001DS', 12, 'MZ2020'
            (VERSION can be blank - but allows multiple versions for the same subject-interval and will be appended to the ID)
             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="..\\sampledata\\mridata")

    args = parser.parse_args()
    inputdir = args.filedir
    print("Input:", inputdir)
    # Output of all vars
    allprint = False
    if access(inputdir, R_OK):
        # sheet = 1
        skip = 0
        header = None
        tabs = 1
        seriespattern = '*.xlsx'  # originally .csv
        try:
            files = glob.glob(path.join(inputdir, seriespattern))
            print("Files:", len(files))
            for f2 in files:
                print("Loading ", f2)
                etype = 'MRI'
                if 'ASHS'.lower() in f2.lower():
                    etype += ' ASHS'
                elif 'FreeSurf'.lower() in f2.lower():
                    etype += ' FS'
                elif 'TASK'.lower() in f2.lower():
                    etype = 'TASKRET'
                    # sheet = 0
                    tabs = 3  # Data upload file has 3 tabs: Bind, Bind3, Bind5
                elif 'FMRI'.lower() in f2.lower():
                    etype = 'FMRI'
                    # sheet = 0
                else:
                    raise ValueError("Cannot determine MRI type from filename: requires one of ASHS, FreeSurf, FMRI in the xlsx filename")
                msg = "Running %s" % etype
                print(msg)
                for tab in range(tabs):
                    sheet = tab
                    dp = MridataParser(f2, sheet, skip, header, etype)
                    xsd = dp.getxsd()[etype]
                    print('XSD: %s' % xsd)
                    for sd in dp.subjects:
                        for i, row in dp.subjects[sd].iterrows():
                            msg = '**SubjectID: %s Visit: %dm' % (sd, int(row['interval']))
                            print(msg)
                            sampleid = dp.getSampleid(sd, row)
                            print(sampleid)
                            # Print every field value for every subject
                            if allprint:
                                for ctab in dp.fields:
                                    if ctab in row:
                                        msg1 = "Field: %s = %s" % (ctab, str(row[ctab]))
                                        print(msg1)
                            # Print XNAT upload data for every subject
                            (mandata, motdata) = dp.mapData(row, i, xsd)
                            print(mandata)
                            print(motdata)
                        # just print one subject for testing
                        break

        except Exception as e:
            print("ERROR: ", e)
    else:
        print("Cannot access directory: ", inputdir)
