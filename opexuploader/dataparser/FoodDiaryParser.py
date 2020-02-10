
"""

    Title: Food Diary Parser
    Programmer: Alan Ho
    Description: Parses food diary stuff
    Date created: 25/09/2018

    Notes: This parses food diary data for upload


    Last modified: 26/09/2018



(c) Alan Ho


"""
###
from os.path import join

import numpy as np

from opexuploader.dataparser.abstract.DataParser import DataParser


class FoodDiaryParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        self.get_data()
        self.sortSubjects('Subject')

    def get_data(self):
        df = self.data
        df.dropna(axis='rows', inplace=True)
        df['Subject'], df['interval'] = ('', '')
        for i in df.index:
            df.loc[i, 'Subject'], df.loc[i, 'interval'] = df['ID'].str.split('_')[i]

        df['Subject'] = df['Subject'].apply(lambda x: ''.join(x.split()))
        df = df[df['interval'] != 'CO-1']

        interval_dict = {'BL': 0, '3M': 3, '6M': 6, '9M': 9, '12M': 12}
        df = df.replace({'interval': interval_dict})

        df[self.fields] = df[self.fields].astype('float')

        self.data = df

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
            xsd + '/sample_id': '',  # row number in this data file for reference
            xsd + '/sample_quality': 'Unknown',  # default - check later if an error
            xsd + '/data_valid': 'Initial'
        }

        motdata = {}
        for field in self.fields:
            if field in row and not np.isnan(row[field]):
                motdata[xsd + '/' + field] = str(row[field])

        # motdata['opex:fooddiary/weight'] = str(row['weight'])

        return (mandata,motdata)

    def getxsd(self):
        return "opex:fooddiary"


    def getSampleid(self,sd, row):
        """
        Generate a unique id for data sample
        :param row:
        :return:
        """
        try:
            id = "FD" + "_" + sd + "_" + str(row['interval']) + 'M'
        except:
            raise ValueError('Cannot find Interval')
        return id


###############################
if __name__ == '__main__':
    inputdir = 'Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\fooddiary'
    inputfile = 'Foodworks Data Entry 19.07.18.xlsx'
    sheet = 0
    header = None
    skip = 1
    etype = 'FD'
    dp = FoodDiaryParser(join(inputdir, inputfile), sheet, skip, header)
    dp.getxsd()
    print(dp.fields)

    # for sd in dp.subjects:
    #     for i, row in dp.subjects[sd].iterrows():
    #         (mandata, data) = dp.mapData(row, i)
    #         print(data)

