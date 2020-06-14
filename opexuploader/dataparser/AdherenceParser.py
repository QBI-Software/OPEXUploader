"""
Title:      Adherence Parser
Author:     Alan Ho
Date:       26/03/2019
Description:    Parses adherence rates and HRs from training diaries

Developer Notes:

1. Consider making separate parser for the LIT group
2. Add the XnatConnector functionality to look up a specific cosmed HR value
"""
from __future__ import print_function

import argparse
import glob
import os
import re
from os.path import basename, join, expanduser

import numpy as np
import pandas as pd

from opexuploader.dataparser.abstract.DataParser import DataParser
from xnatconnect.XnatConnector import XnatConnector


class AdherenceParser(DataParser):

    def __init__(self, *args):
        DataParser.__init__(self, *args)
        self.training_file = pd.ExcelFile(self.datafile)
        self.type = re.findall('(?<=Diary-)[A-Z]{3}', basename(self.datafile))[0]
        self.extraction = {'AIT': extract_AIT, 'MIT': extract_MIT, 'LIT': extract_LIT}
        self.getData()


    def getData(self):
        pattern = '^[:0-9:]{4}[:A-Z:]{2}$'
        subject_sheets = [sheet for sheet in self.training_file.sheet_names if re.match(pattern, sheet)]

        self.subjects = {}
        self.df = {}
        for sheet in subject_sheets:

            print(sheet + '-------------------')
            try:
                extract = self.extraction[self.type](self.training_file, sheet)
                self.subjects[extract.subject] = extract.data
                self.df[extract.subject] = extract.df
                # self.errors[extract.subject] = extract.errors

            except Exception as e:
                print(("ERROR:", e))


    def getSampleid(self, sd):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'ADHERE_' + sd
        return id

    def mapData(self, row, xsd=None):

        if xsd is None:
            xsd = self.getxsd()

        mandata = {
            # xsd + '/date': str(self.date),
            xsd + '/interval': str(0),
            xsd + '/sample_id': '',  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': ''
        }

        motdata = {}
        for field in self.fields:
            motdata[xsd + '/' + field] = str(row[field].iloc[0])

        return (mandata, motdata)


class extract_AIT:

    def __init__(self, training_file, sheet):

        self.training_file = training_file
        self.subject = sheet
        self.get_data()
        self.cut_sessions()
        #
        self.sum_df03 = self.compute_HRave(self.df03)
        self.sum_df46 = self.compute_HRave(self.df46)
        self.concat()

        # self.detect_errors(self.df)
        self.compute_sum()

    def get_data(self):
        self.df = pd.read_excel(self.training_file, self.subject, header=[2, 3, 4]).reset_index()

    def cut_sessions(self):
        session = self.extract_session(self.df)

        cut1 = session[session == 36].index[0]
        cut2 = session[session == 37].index[0]
        cut3 = session[session == 72].index[0]

        self.df03 = self.df.iloc[:(cut1 + 1)]
        self.df46 = self.df.iloc[cut2:(cut3 + 1)]

    def extract_session(self, df):
        session_level = [col for col in df.columns.levels[0] if bool(re.match('[0-9]{1,3}\-[0-9]{1,3}', col))][0]
        session = df[session_level]['Session'].iloc[:, 0]

        return session

    def compute_HRave(self, df):

        session = self.extract_session(df)
        self.session = session

        levels = df.columns.levels[0].tolist()
        active = [col for col in levels if 'Active' in col]
        interval = [col for col in levels if 'Interval' in col]

        THR_min = [col for col in df.columns.levels[0] if bool(re.match('(Minutes).*(THR)', col))][0]

        recovery = {}
        for col in active:
            x = df[col]['HR (bpm)'].iloc[:, 0]
            x.astype(float, inplace=True)
            recovery[col] = x

        self.recovery_df = recovery
        self.recovery_sum = pd.DataFrame(recovery).sum(axis=1) * 3

        intervals = {}
        temp_data = {}
        for col in interval:
            minutes = [level2 for level2 in df[col].columns.levels[0] if 'minute' in level2]
            intervals[col] = {}
            for min in minutes:
                x = df[col][min]['HR (bpm)']
                intervals[col][min] = x

            temp_data[col] = pd.DataFrame(intervals[col]).sum(axis=1)

        self.interval_df = pd.DataFrame(temp_data)
        self.interval_sum = self.interval_df.sum(axis=1)

        session_ave = pd.DataFrame({
            'Subject': self.subject,
            'Session': session,
            'HR_ave': (self.interval_sum + self.recovery_sum)/25,
            'THR_min': df[THR_min].iloc[:, 0].astype(float)
        }).set_index(['Subject'])

        return (session_ave)

    def concat(self):
        self.df = pd.concat([self.df03, self.df46])

        self.sum_df = pd.concat([self.sum_df03, self.sum_df46])
        self.sum_df['month'] = ''
        self.sum_df['month'][self.sum_df['Session'] < 37] = 'HR_ave03'
        self.sum_df['month'][self.sum_df['Session'] >= 37] = 'HR_ave46'

    def compute_sum(self):
        self.data = self.sum_df.pivot_table(values='HR_ave',
                               index=['Subject', 'month'],
                               aggfunc=np.mean).unstack()['HR_ave'].\
                        assign(THR_min_ave=self.sum_df['THR_min'].mean(),
                               THR_min_percent=self.sum_df['THR_min'].mean()/8 * 100).\
                        reset_index()

        self.data['HR_max0'] = get_maxHR(self.subject)[0]
        self.data['HR_max3'] = get_maxHR(self.subject)[1]

        self.data['HR_maxp03'] = (self.data['HR_ave03'] / self.data['HR_max0']) * 100
        self.data['HR_maxp46'] = (self.data['HR_ave46'] / self.data['HR_max3']) * 100


class extract_MIT(extract_AIT):

    def __init__(self, *args, **kwargs):
        extract_AIT.__init__(self, *args, **kwargs)


    def get_data(self):
        self.df = pd.read_excel(self.training_file, self.subject, header=3).reset_index()

    def extract_session(self, df):
        session = df['Session']
        return session

    def compute_HRave(self, df):

        session = self.extract_session(df)

        columns = [col for col in df.columns if not isinstance(col, int)]
        HR_columns = [col for col in columns if 'HR' in col and not bool(re.search('Pre',col))]

        # remove the warm up and cool down
        HR = df[HR_columns[1:(len(HR_columns)-1)]].mean(axis=1)

        print(df[HR_columns[1:(len(HR_columns)-1)]])
        THR_min = df['Unnamed: 40']

        session_ave = pd.DataFrame({
            'Subject': self.subject,
            'Session': session,
            'HR_ave': HR,
            'THR_min': THR_min.astype(float)
        }).set_index(['Subject'])

        return (session_ave)

    def concat(self):

        self.df = pd.concat([self.df03, self.df46])

        self.sum_df = pd.concat([self.sum_df03, self.sum_df46])
        self.sum_df['month'] = ''
        self.sum_df['month'][self.sum_df['Session'] < 37] = 'HR_ave03'
        self.sum_df['month'][self.sum_df['Session'] >= 37] = 'HR_ave46'

    def compute_sum(self):
        self.data = self.sum_df.pivot_table(values='HR_ave',
                               index=['Subject', 'month'],
                               aggfunc=np.mean).unstack()['HR_ave'].\
                        assign(THR_min_ave=self.sum_df['THR_min'].mean(),
                               THR_min_percent=self.sum_df['THR_min'].mean()/40 * 100).\
                        reset_index()

        self.data['HR_max0'] = get_maxHR(self.subject)[0]
        self.data['HR_max3'] = get_maxHR(self.subject)[1]

        self.data['HR_maxp03'] = (self.data['HR_ave03'] / self.data['HR_max0']) * 100
        self.data['HR_maxp46'] = (self.data['HR_ave46'] / self.data['HR_max3']) * 100


class extract_LIT(extract_MIT):

    def __init__(self, *args, **kwargs):
        extract_MIT.__init__(self, *args, **kwargs)

    def compute_HRave(self, df):

        session = self.extract_session(df)

        columns = [col for col in df.columns if not isinstance(col, int)]
        HR_columns = [col for col in columns if 'HR' in col and not bool(re.search('Pre',col))][:-1]

        # remove the warm up and cool down

        HR = df[HR_columns[1:(len(HR_columns)-1)]].mean(axis=1)

        THR_min = df['Minutes in THR Zone']

        session_ave = pd.DataFrame({
            'Subject': self.subject,
            'Session': session,
            'HR_ave': HR,
            'THR_min': THR_min.astype(float)
        }).set_index(['Subject'])
        return (session_ave)


def get_maxHR(subject):
    home = expanduser("~")
    configfile = join(home, '.xnat.cfg')
    xnat = XnatConnector(configfile, 'opex')
    xnat.connect()

    criteria = [('xnat:subjectData/SUBJECT_ID', 'LIKE', '*'), 'AND']
    columns = ['xnat:subjectData/SUBJECT_LABEL', 'opex:cosmed/INTERVAL', 'opex:cosmed/HR']
    dsitype = 'opex:cosmed'

    subj = xnat.conn.select(dsitype, columns).where(criteria)
    xnat.conn.disconnect()

    df = pd.DataFrame(list(subj)).\
                        set_index(['xnat_subjectdata_subject_label', 'interval']).\
                        loc[subject]

    HR_max0, HR_max3 = float(df.loc['0']), float(df.loc['3'])

    return HR_max0, HR_max3

def get_errors(dp):
    keycolumns = ['Session', 'HR', 'HR.1', 'HR.2', 'HR.3', 'HR.4', 'HR.5', 'HR.6', 'HR.7']
    df = pd.concat(dp.df)[keycolumns]. \
        reset_index(). \
        drop('level_1', axis=1). \
        set_index(['level_0', 'Session'])

    condition = (((df > 0) & (df < 50)) | (df > 200)).any(axis=1)

    return df[condition]

# inputdir = "Q:\\DATA\\DATA ENTRY\\Training Diaries"
# files = 'Training-Diary-AIT_20181123.xlsx'
# path = join(inputdir, files)
# dp = extract_AIT(training_file=path, sheet='1001DS')
#


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Adherence Parser',
                                     description='''\
        This parses THR zone minutes / percent, HRmax data from the training diaries taking data from cosmed
         ''')
    parser.add_argument('--inputdir', help='Directory of training diaries', default="Q:\\DATA\\DATA ENTRY\\Training Diaries")
    parser.add_argument('--trainingfile', help='Optional (parse a particular training diary')

    args = parser.parse_args()

    inputdir = args.inputdir
    print("Input:", inputdir)
    if os.access(inputdir, os.R_OK):
        seriespattern = 'Training-Diary-*.xlsx'

        try:
            files = glob.glob(join(inputdir, seriespattern))
            print("Files:", len(files))
            for f2 in files:
                print("\n****Loading", f2)
                dp = AdherenceParser(f2)
                dp.sortSubjects()
                for sd in dp.subjects:
                    sampleid = dp.getSampleid(sd)
                    print('Sample ID: ' + sampleid)
                    row = dp.subjects[sd]
                    (mandata, motdata) = dp.mapData(row)
                    print(motdata)
        except ValueError as e:
            print(e)

    else:
        print("Cannot access directory: ", inputdir)

