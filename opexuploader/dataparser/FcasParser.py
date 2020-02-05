import os
from os.path import join, splitext
import pandas as pd
import re
import sys
import numpy as np
import argparse

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser

# path = r'Q:\DATA\DATA ENTRY\XnatUploaded\sampledata\fcas'
# filename = 'FCAS_1001DS_20180727.xlsx'

class FcasParser(DataParser):

    def __init__(self, inputdir, filename, *args):
        DataParser.__init__(self, *args)
        self.inputdir = inputdir
        self.filename = filename
        self.get_date()
        self.fields = ['q' + str(i) for i in range(1,42)]
        self.fields_comments = ['q42a', 'q42b', 'q42c']
        self.score_fcas()
        self.sortSubjects(subjectfield='Subject')

    def get_date(self):
        from datetime import datetime
        date = re.split('_', self.filename)[2]
        self.date = datetime.strptime(splitext(date)[0], '%Y%m%d').strftime('%Y-%m-%d')

    def score_fcas(self):
        pathtofile = join(self.inputdir, self.filename)

        scoring = {
            "Never did this activity": 1,
            "Not in the past year": 2,
            "Less than once per month": 3,
            "1 to 4 times per month": 4,
            "5 or times per month": 5,
            '5 times or more per month': 5,
            '5 or more times per month': 5,
            "Every day": 6
        }

        x1 = pd.ExcelFile(pathtofile)

        data_list = []
        for sheet in x1.sheet_names:

            data = pd.read_excel(pathtofile, sheet_name=sheet)
            data.columns = ['Quest_no', 'Question', 'Never did this activity', 'Not in the past year', 'Less than once per month', '1 to 4 times per month	', '5 or times per month', 'Every day', 'Specify']

            if not all(data.set_index(['Quest_no', 'Question']).isna().all()):

                specify = data.query('Question == "Other, please specify"')['Specify'].reset_index()
                specify['Quest_no'] = ['q42a', 'q42b', 'q42c']
                specify['Subject'] = re.split('_', self.filename)[1]
                specify = specify.pivot(index='Subject', columns='Quest_no', values='Specify').reset_index()


                questions = data.iloc[0:41].set_index(['Quest_no', 'Question']).stack().reset_index()
                questions['Subject'] = re.split('_', self.filename)[1]
                questions['Question'] = questions['Question'].str.rstrip()
                questions['level_2'] = questions['level_2'].str.rstrip()
                questions['Quest_no'] = questions['Quest_no'].apply(lambda x: 'q' + str(int(x)))
                questions.replace({'level_2': scoring}, inplace=True)
                questions = questions.pivot(index='Subject', columns='Quest_no', values='level_2').reset_index()

                alldata = pd.merge(questions, specify, on='Subject')
                alldata['interval'] = re.findall('\\d*', sheet.strip())[0]

                data_list.append(alldata)
            else:
                continue


        self.data = pd.concat(data_list)

    def mapData(self, row, i, xsd=None):
        """
        Maps required fields from input rows
        :param row:
        :return:
        """
        if xsd is None:
            xsd = self.getxsd()

        mandata = {
            xsd + '/interval': str(row['interval']),
            xsd + '/date': self.date,
            xsd + '/sample_id': '',  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial'
        }

        motdata = {}
        for field in self.fields:
            if field in row and not np.isnan(float(row[field])):
                motdata[xsd + '/' + field] = str(row[field])

        for field in self.fields_comments:
            motdata[xsd + '/' + field] = str(row[field])

        return (mandata, motdata)

    def getxsd(self):
        return "opex:fcas"

    def getSampleid(self, sd, row):
        """
        Generate a unique id for data sample
        :param row:
        :return:
        """
        try:
            id = "FCAS" + "_" + sd + "_" + str(row['interval']) + 'M'
        except:
            raise ValueError('Cannot find Interval')
        return id


#####

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
                Reads files in a directory and extracts data for upload to XNAT

                 ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\fcas\\test")
    parser.add_argument('--datafile', action='store', help='Filename of original data',
                        default="IPAQ_20180913_XNATREADY.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract',
                        default="0")
    args = parser.parse_args()

    inputdir = args.filedir
    skip = args.sheet
    files = [f for f in os.listdir(inputdir) if splitext(f)[1] == '.xlsx']

    for f2 in files[0:20]:
        print(f2)
        try:
            dp = FcasParser(inputdir=inputdir, filename=f2)
            for sd in dp.subjects:
                for i,row in dp.subjects[sd].iterrows():
                    (mandata, data) = dp.mapData(row, i)
                    print((mandata, data))

        except ValueError as e:
            print(e)

