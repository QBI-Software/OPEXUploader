
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
import os
from os.path import join
import glob
import pandas as pd
import re
import sys
import numpy as np
import argparse

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser, stripspaces

class FoodDiaryParser(DataParser):
    def __init__(self, *args):
        DataParser.__init__(self, *args)
        # self.fields you need to consider adding the fields from the config db here
        self.get_data()
        fields = pd.read_csv(r'C:\Users\uqaho4\PycharmProjects\OPEXUploader\resources\fields\fooddiary_fields.csv')
        # self.fields = [f.tolist()[0] for f in fields.values]
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

        ########
        path = r'resources\fooddiary_fields.csv'
        # self.fields = pd.read_csv(path).iloc[:, 0].tolist()
        # self.fields = [x for x in df.columns if x not in ['ID', 'Subject', 'interval']]

        # self.fields = ['alcoholic']
        self.fields = [
            "weight",
            "energy",
            "protein",
            "total_fat",
            "sat_fat",
            "trans_facid",
            "poly_fat",
            "mono_fat",
            "cholesterol",
            "carbohydrate",
            "sugars",
            "starch",
            "water",
            "alcohol",
            "fibre",
            "ash",
            "thiamin",
            "ribofavin",
            "niacin",
            "niacin_eq",
            "vitamin_c",
            "vitamin_e",
            "toco_alpha",
            "vitamin_b6",
            "vitamin_b12",
            "total_folate",
            "folic_acid",
            "folate_food",
            "folate_DFE",
            "vitamin_a",
            "retinol",
            "beta_carotine_eq",
            "beta_carotine",
            "sodium",
            "potassium",
            "magnesium",
            "calcium",
            "phosphorus",
            "iron",
            "zinc",
            "selenium",
            "iodine",
            "protein_kjpercent",
            "fat_kjpercent",
            "satfat_kjpercent",
            "transfat_kjpercent",
            "carb_kjpercent",
            "alcohol_kjpercent",
            "fibre_kjpercent",
            "others_kjpercent",
            "monofat_percent",
            "polyfat_percent",
            "satfat_percent",
            "n3fattyacid",
            "F18D2CN6",
            "F18D3N3",
            "F20D5N3",
            "F22D5N3",
            "F22D6N3",
            "tryptophan",
            "grains",
            "grains_refined",
            "wholegrains",
            "wholegrains_percent",
            "fruit",
            "citrus",
            "other_fruit",
            "fruit_juice",
            "fruit_juice_percent",
            "vegetables",
            "dark_green_vegetables_serve",
            "red_vegetables",
            "tomatoes",
            "other_RO_vegetables",
            "starchy_vegetables",
            "potatoes",
            "other_starchy_vegetables_serve",
            "starchy_vegetables_percent",
            "legumes",
            "other_vegetables",
            "protein_foods",
            "red_meats",
            "poultry",
            "eggs",
            "processed_meats",
            "organ_meats",
            "seafood_high",
            "seafood_low",
            "nuts_seeds_serve",
            "legumes_protein",
            "soy_products",
            "dairy",
            "milk",
            "cheese",
            "yoghurt",
            "milk_alternatives",
            "oil",
            "solid_fat",
            "added_sugars",
            "added_sugars_kj",
            "added_sugars_percent",
            "alcoholic",
            "unclassified_wt",
            "unclassified_wt_percent",
            "unclassified_kj",
            "unclassified_kj_percent",
            "caffeine"
        ]
        # # columns = pd.read_csv(path).iloc[:,1].tolist()
        #
        # rename_dict = {}
        # for i in range(0, len(columns)):
        #     rename_dict[columns[i]] = self.fields[i]
        #
        # print(df.head())
        # df = df.rename(columns=rename_dict)
        # print(df.head())
        # df.columns = ['ID', 'Subject', 'interval']
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
    print((dp.fields))

    # for sd in dp.subjects:
    #     for i, row in dp.subjects[sd].iterrows():
    #         (mandata, data) = dp.mapData(row, i)
    #         print(data)

