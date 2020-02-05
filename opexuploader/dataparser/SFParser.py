
"""

    Title: SF-36 Parser
    Programmer: Alan Ho
    Description: Parses, scores and uploads raw SF-36 data (see README for more information)
    Date created: 24/09/2018

    Notes:
        scoring guide taken from https://www.rand.org/health/surveys_tools/mos/36-item-short-form/scoring.html

        - All items scored so high score is more favorable health state
        - Each item scored from 0 - 100 range so that lowest and highest scoress are 0 and 100, respectively
        Scores represent the percentage of total possible score achieved
        - Items from same scale are averaged together to create 8 scale scores:
            'PF' = 'Physical Health': 10 items
            'RF' = 'Role functioning/physical': 4 items
            'Role functioning/emotional': 3 items
            'Energy/fatigue': 4 items
            'Emotional well-being': 5 items
            'Social functioning': 2 items
            'Pain': 2 items
            'General Health': 5 items
            'Health change': 1 item


    Last modified: 24/09/2018

(c) Alan Ho


"""

from os import getcwd
from os.path import join
import glob
import pandas as pd
import re
import sys
import numpy as np

sys.path.append(getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser, stripspaces


class SF36Parser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)

        # self.convertScores()
        # self.scoreSF()

        # pop_fields = ['GenPop_PF', 'GenPop_RP', 'GenPop_BP', 'GenPop_GH', 'GenPop_VT', 'GenPop_SF', 'GenPop_RE',
                      # 'GenPop_MH', 'GenPop_PCS', 'GenPop_MCS']

        self.fields = ['PF', 'RP', 'BP', 'GH', 'VT', 'SF', 'RE', 'MH', 'PCS', 'MCS']

        df = self.data
        df[['Subject', 'interval']] = df.pop('RecordID').str.split('\\s', 1, expand=True)
        df['interval'] = df['interval'].apply(extract_interval)
        # df['Subject'] = df['Subject'].apply(lambda x: getID(x))
        self.data = df
        # self.data = df[['Subject', 'interval'] + self.fields]

        self.sortSubjects('Subject')


    def convertScores(self):

        cols = self.data.columns.tolist()
        start = cols.index('GH01')
        end = start + 36
        q_num = pd.Series(self.data.columns[start:end], index=list(range(1, 37, 1))) # extract question number

        map_scoring = {}
        for i in range(1, 37, 1):
            name = q_num[i]
            map_scoring[name] = score(str(i))

        self.data = self.data.replace(map_scoring)


    def scoreSF(self):
        subscales = ['PF', 'RP', 'BP', 'GH', 'VT', 'SF', 'RE', 'MH']

        self.fields = []
        for s in subscales:
            self.data[s] = self.data.filter(regex=('({}.*)+(\\d+)'.format(s))).mean(axis=1)
            self.fields.append(s)


    def getSampleid(self, sd, row):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'SF' + '_' + sd + '_' + str(row['interval']) + 'M'
        return id

    def mapData(self, row, i, xsd):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """

        mandata = {
            xsd + '/interval': str(row['interval']),
            xsd + '/sample_id': str(i),  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': ''
        }

        motdata = {}
        for field in self.fields:
            if field in row and not np.isnan(row[field]):
                mandata[xsd + '/' + field] = str(row[field])
        return (mandata, motdata)

    def validData(self, dvalues):
        """
        Checks data is present in list
        -	-	-

        :param dvalues:
        :return:
        """
        rtn = True
        if isinstance(dvalues, list):
            for d in dvalues:
                if isinstance(d, str) or isinstance(d, str):
                    rtn = False
                    break

            if all([np.isnan(d) for d in dvalues]):
                rtn = False

        return rtn



def score(q):
    def find_q(string, q):
        return any([q == s.strip() for s in re.split(',', string)])

    scoring_dict = {
        '1, 2, 20, 22, 34, 36': {1: 100, 2: 75, 3: 50, 4: 25, 5: 0},
        '3, 4, 5, 6, 7, 8, 9, 10, 11, 12': {1: 0, 2: 50, 3: 100},
        '13, 14, 15, 16, 17, 18, 19': {1: 0, 2: 100},
        '21, 23, 26, 27, 30 ': {1: 100, 2: 80, 3: 60, 4: 40, 5: 20, 6: 0},
        '24, 25, 28, 29, 31': {1: 0, 2: 20, 3: 40, 4: 60, 5: 80, 6: 100},
        '32, 33, 35': {1: 0, 2: 25, 3: 50, 4: 75, 5: 100}
    }

    index = [k for k in list(scoring_dict.keys()) if find_q(k, q)][0]

    return scoring_dict[index]

def extract_interval(interval):
    if 'Baseline' in interval:
        interval = 0
    else:
        interval = int(re.findall('\\d+', interval)[0])

    return interval

# inputdir = r'Q:\WORKING DATA\SF-36\1. Raw Files'
# inputfile = "SF-36 Data 5_09_18_SCORED.xls"
# sheet = 0
# skip= 0
# etype = None
# header = 0
# dp = SF36Parser(join(inputdir, inputfile), sheet, skip, header, etype)
# dp.data[['Subject','interval', 'PF02']]
#
#
# q = pd.Series(dp.data.columns[0:36], index=range(1,37,1))
# dp.data.replace(map_scoring)
#
#
# map_scoring = {}
# for i in range(1,37,1):
#     name = q[i]
#     map_scoring[name] = scoring(str(i))
#
# dp.data.replace()
# [{q[i]:scoring(str(i))} for i in range(1,37,1)]
#
# scoring('2')
#
# scoring(questions[1])
#
#
# def scoring(q):
#     # q = re.findall('(?<=\\d)\\d+', question)[0]
#
#     def find_q(string, q):
#         return any([q == s.strip() for s in re.split(',', string)])
#
#     scoring_dict = {
#         '1, 2, 20, 22, 34, 36': {1: 100, 2: 75, 3: 50, 4: 25, 5: 0},
#         '3, 4, 5, 6, 7, 8, 9, 10, 11, 12': {1: 0, 2: 50, 3: 100},
#         '13, 14, 15, 16, 17, 18, 19': {1: 0, 2: 100},
#         '21, 23, 26, 27, 30 ': {1: 100, 2: 80, 3: 60, 4: 40, 5: 20, 6: 0},
#         '24, 25, 28, 29, 31': {1: 0, 2: 20, 3: 40, 4: 60, 5: 80, 6: 100},
#         '32, 33, 35': {1: 0, 2: 25, 3: 50, 4: 75, 5: 100}
#     }
#
#     index = [k for k in scoring_dict.keys() if find_q(k, q)][0]
#
#     return scoring_dict[index]

# def scoring(question):
#     q = re.findall('(?<=\\d)\\d+', question)[0]
#
#     def find_q(string, q):
#         return any([q == s.strip() for s in re.split(',', string)])
#
#     scoring_dict = {
#         '1, 2, 20, 22, 34, 36': {1: 100, 2: 75, 3: 50, 4: 25, 5: 0},
#         '3, 4, 5, 6, 7, 8, 9, 10, 11, 12': {1: 0, 2: 50, 3: 100},
#         '13, 14, 15, 16, 17, 18, 19': {1: 0, 2: 100},
#         '21, 23, 26, 27, 30 ': {1: 100, 2: 80, 3: 60, 4: 40, 5: 20, 6: 0},
#         '24, 25, 28, 29, 31': {1: 0, 2: 20, 3: 40, 4: 60, 5: 80, 6: 100},
#         '32, 33, 35': {1: 0, 2: 25, 3: 50, 4: 75, 5: 100}
#     }
#
#     index = [k for k in scoring_dict.keys() if find_q(k, q)][0]
#
#     return scoring_dict[index]
#
# cols = dp.data.filter(regex='(GH.*)+\\d{2}').columns
# for c in cols:
#     print(dp.data.replace({c: scoring(c)})[c].unique())
#
#
# dp.data.replace({'GH03': scoring('GH03')})['GH03'].unique()
# scoring('GH01')
#
#
# def find_q(string, q):
#     return any([q == s.strip() for s in re.split(',', string)])
#
# scoring_dict = {
#     '1, 2, 20, 22, 34, 36': {1: 100, 2: 75, 3: 50, 4: 25, 5: 0},
#     '3, 4, 5, 6, 7, 8, 9, 10, 11, 12': {1: 0, 2: 50, 3: 100},
#     '13, 14, 15, 16, 17, 18, 19': {1: 0, 2: 100},
#     '21, 23, 26, 27, 30 ': {1: 100, 2: 80, 3: 60, 4:40, 5:20, 6: 0},
#     '24, 25, 28, 29, 31': {1: 0, 2: 20, 3: 40, 4: 60, 5: 80, 6: 100},
#     '32, 33, 35': {1: 0, 2: 25, 3: 50, 4: 75, 5: 100}
# }
#
#
#
# find_q('5')
#
#
# [k for k in scoring_dict.keys() if find_q(k, '5')]
#
# for k in scoring_dict.keys():
#     print('32' in k)
#
# string = '3, 4, 45, 6, 7, 8, 9, 10, 11, 12'
# any(['5' == s.strip() for s in re.split(',', string)])
#
#
# re.split(',', '3, 4, 5, 6, 7, 8, 9, 10, 11, 12')
#
# [k for k in scoring_dict.keys() if '5' in k]
#
# '32' in scoring_dict.keys()[0]
#
# dp.data.replace({'GH01': dict1})['GH01'].head()
#
# dp.data.head()['GH01']

###########################

if __name__ == '__main__':
    inputdir = r'Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\sf36'
    inputfile = "SF-36 Data 17_09_18_SCORED_2.xls"
    sheet = 0
    skip= 0
    etype = 'SF36'
    header = 0
    dp = SF36Parser(join(inputdir, inputfile), sheet, skip, header, etype)

    # for sd in dp.subjects:
    for i, row in dp.subjects['1191GH'].iterrows():
        j = row['interval']
        sampleid = dp.getSampleid('1191GH', row)
        print(('Sampleid:', sampleid))
        (mandata, data) = dp.mapData(row, i, 'opex:SF36')
        print(mandata)
        print(data)


    # print(dp.data.filter(regex='(Subject)|(interval)|(PF)').head())

    # data = dp.data.replace({'PF10': dp.convertScores()['PF10']})
    # print(data.filter(regex='(Subject)|(interval)|(PF)').head())

    # print(skip)
    # print(dp.data.head())
    # print(dp.getSampleid('1001DS', 0))
    # # xsd = dp.getxsd()
    # for sd in dp.subjects:
    #     for i, row in dp.subjects[sd].iterrows():
    #         j = row['interval']
    #         sampleid = dp.getSampleid(sd, j)
    #         print('Sampleid:', sampleid)
    #         (mandata, data) = dp.mapData(row, j, 'opex:SF36')
    #         print(mandata)
    #         print(data)




