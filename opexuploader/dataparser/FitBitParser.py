"""

    Fitbit parser 1: reads raw fitbit from csv / xlsx, computes intervals, summarises it across intervals,
    then saves to file

    Alan Ho (copyright)

"""

import argparse
import os
import re
import sys
from os.path import join

import numpy as np
import pandas as pd

sys.path.append(os.getcwd())
from opexuploader.dataparser.abstract.DataParser import DataParser, stripspaces
from datetime import datetime
from shutil import copyfile


class FitBitParser(DataParser):
    def __init__(self, file, schema_path):
        self.file = file
        self.headers = pd.read_csv(schema_path)['Variable']
        self.fields = pd.read_csv(schema_path)['Field']
        self.types = pd.read_csv(schema_path)['Type']
        self.subject = os.path.basename(os.path.dirname(self.file))

    def read_raw(self):
        self.data = pd.read_excel(self.file)
        return self.data

    def get_data(self):
        def enumerate_index(list):
            return [i for i, x in enumerate(list) if x == True][0]

        def line_strip(line):
            line = re.findall(r'\"(.+?)\"', line)

            return np.array(line)

        # this processes .xlsx and .csv files
        if os.path.splitext(self.file)[1] == '.xlsx':

            self.read_raw()

            heading_list = [all(i in self.data.apply(tuple, axis=1)[row] for i in tuple(self.headers)) for row in
                            range(0, len(self.data))]
            header_index = enumerate_index(heading_list)

            dat = self.data.iloc[(header_index + 1):(len(self.data))]
            dat.columns = self.data.iloc[header_index]
            dat.reset_index(drop=True, inplace=True)
            dat.columns.name = ''

            na_list = [all(pd.isnull(item) for item in dat.apply(tuple, axis=1)[row]) for row in range(0, len(dat))]
            na_index = enumerate_index(na_list)

            self.data = dat.iloc[0:na_index]

        elif os.path.splitext(self.file)[1] == '.csv':

            head_concat = ','.join(str(e) for e in self.headers)
            line_list = [line.rstrip('\n') for line in open(self.file, 'r')]
            line_list = line_list[line_list.index(head_concat):]
            line_list = line_list[:line_list.index('')]

            df = np.stack([line_strip(line) for line in line_list[1:]])
            self.data = pd.DataFrame(df).apply(lambda x: x.str.replace(',', ''))

        self.data.columns = self.fields
        self.data = self.data.astype(dict(list(zip(self.fields, self.types))))
        self.data['Subject'] = self.subject
        self.data['date'] = self.data['date'].str.split().str[0]
        self.data['date'] = pd.to_datetime(self.data['date'])
        self.data['file'] = self.file

        return self.data


class data_finder:
    def __init__(self, file, schema_path):
        self.file = file
        self.headers = pd.read_csv(schema_path)['Variable']
        self.fields = pd.read_csv(schema_path)['Field']
        self.types = pd.read_csv(schema_path)['Type']
        self.subject = os.path.basename(os.path.dirname(self.file))

    def read_raw(self):
        self.data = pd.read_excel(self.file)
        return self.data

    def get_data(self):
        def enumerate_index(list):
            return [i for i, x in enumerate(list) if x == True][0]

        def line_strip(line):
            line = re.findall(r'\"(.+?)\"', line)

            return np.array(line)

        # this processes .xlsx and .csv files
        if os.path.splitext(self.file)[1] == '.xlsx':

            self.read_raw()

            heading_list = [all(i in self.data.apply(tuple, axis=1)[row] for i in tuple(self.headers)) for row in
                            range(0, len(self.data))]
            header_index = enumerate_index(heading_list)

            dat = self.data.iloc[(header_index + 1):(len(self.data))]
            dat.columns = self.data.iloc[header_index]
            dat.reset_index(drop=True, inplace=True)
            dat.columns.name = ''

            na_list = [all(pd.isnull(item) for item in dat.apply(tuple, axis=1)[row]) for row in range(0, len(dat))]
            na_index = enumerate_index(na_list)

            self.data = dat.iloc[0:na_index]

        elif os.path.splitext(self.file)[1] == '.csv':

            head_concat = ','.join(str(e) for e in self.headers)
            line_list = [line.rstrip('\n') for line in open(self.file, 'r')]
            line_list = line_list[line_list.index(head_concat):]
            line_list = line_list[:line_list.index('')]

            df = np.stack([line_strip(line) for line in line_list[1:]])
            self.data = pd.DataFrame(df).apply(lambda x: x.str.replace(',', ''))

        self.data.columns = self.fields
        self.data = self.data.astype(dict(list(zip(self.fields, self.types))))
        self.data['Subject'] = self.subject
        self.data['date'] = self.data['date'].str.split().str[0]
        self.data['date'] = pd.to_datetime(self.data['date'])
        self.data['file'] = self.file

        return self.data


# class FitbitParser(DataParser):
#

def folder_check(path):
    return os.path.basename(os.path.dirname(path))[:4].isdigit()


def filter_by_format(file, pattern="(\\d){4}"):
    pat = re.compile(pattern)
    return bool(pat.match(file))


def get_files(dir):
    def filter_by_format(file, pattern="(\\d){4}"):
        pat = re.compile(pattern)
        return bool(pat.match(file))

    dat_files = os.listdir(dir)

    return [f for f in dat_files if filter_by_format(f)]


def filter_by_format(file, pattern="(\\d){4}"):
    pat = re.compile(pattern)
    return bool(pat.match(file))


def create_cutoffs(inputdir):
    dates = pd.read_excel(join(inputdir, 'Dates.xlsx'))
    dates['Subject'] = dates.apply(lambda x: stripspaces(x, 'ID'), axis=1)
    dates.set_index('Subject', inplace=True)

    intervals = [1, 2, 4, 5]
    for i in intervals:
        cols = [c for c in dates.columns.tolist() if bool(re.search('^{} month'.format(str(i)), c))]
        dates[str(i) + ' month assessment'] = dates[cols].values.max(axis=1)

    assessments = ['Assessment B', 'Training start date'] + [str(i) + ' month assessment' for i in
                                                             list(range(1, 7)) + [9, 12]]
    dates[assessments].to_csv(join(inputdir, 'dates_cutoff.csv'))


class CheckNewFitbit:

    def __init__(self, olddirectory, newdirectory):
        self.olddirectory = olddirectory
        self.newdirectory = newdirectory

        self.oldfiles = getfitbit(self.olddirectory)
        self.newfiles = getfitbit(self.newdirectory)
        self.match()

        print('Old dir: {}'.format(self.olddirectory))
        print('New dir: {}'.format(self.newdirectory))

        print('# Old files {}'.format(len(self.oldfiles)))
        print('# New files {}'.format(len(self.newfiles)))

    def match(self, on='old'):

        oldset = set(self.oldfiles)
        newset = set(self.newfiles)

        if on == 'old':
            self.filesmismatched = []
            for file in (oldset - newset):
                print(file)
                self.filesmismatched.append(file)

        elif on == 'new':
            print(newset - oldset)

    def copy(self):

        for file in self.filesmismatched:
            folder = re.findall('^[:0-9:]{4}[:A-Z:]{2}(?=\_)', file)[0]
            olddir = join(self.olddirectory, folder, file)
            newdir = join(self.newdirectory, folder, file)
            if not os.path.exists(newdir):
                print('copying file {}'.format(file))
                copyfile(olddir, newdir)


def getfitbit(path):
    flatten = lambda l: [item for sublist in l for item in sublist]
    folders = [folder for folder in os.listdir(path)
               if bool(re.match('^[:0-9:]{4}[:A-Z:]{2}$', folder))]

    fileslist = []
    for folder in folders:
        files = [file for file in os.listdir(join(path, folder))
                 if re.match('^[:0-9:]{4}[:A-Z:]{2}.*', file)]
        fileslist.append(files)

    return flatten(fileslist)


## RUNNING on all files that are within subject folders --------------------------
"""
Here we enter the directory path to the fitbit data which then recursively reads all the .csv and .xlsx 
within the Subjects' folders ignoring all the data files not within these folders. 

"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Parse Fitbit Data',
                                     description='''\
               Reads Fitbit data files and puts it into a Xnat ready format. The parser works by choice of schema e.g
               sleep or activities held in respective .csv files in the Fitbit directory. By choosing the activities schema
               the parser will extract the activities data while if the sleep schema is chosen, it will only extract the 
               sleep data. NOTE: the sleep parser will NOT work yet because of the inconsistencies of the schemas across 
               files. 
               
               Will later create an uploader for it once the tables have been created
               

                ''')
    parser.add_argument('--filedir', action='store',
                        help='Directory that contains fitbit folders containing each subject\'s data files',
                        default="Q:\\DATA\\FITBIT DATA")

    parser.add_argument('--schemadir', action='store',
                        help='Indicate the schema .csv file',
                        default="activities_schema.csv")

    parser.add_argument('--outfile', action='store',
                        help='Indicate name and directory of .csv outfile',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\fitbit")

    args = parser.parse_args()

    # ARGUMENTS
    rootdir = args.filedir
    inputschema = os.path.join(rootdir, args.schemadir)
    filename = os.path.join(rootdir, args.outfile)
    outputdir = args.outfile
    inputschema = os.path.join(rootdir, "activities_schema.csv")

    # inputschema = join(path, 'activities_schema.csv')

    files_list = [os.path.join(dp, f) for dp, dn, fn in os.walk(join(rootdir, 'Main_P1')) for f in fn]
    files = [file for file in files_list if folder_check(file) == True]

    print("***********Processing files in %s" % rootdir)

    # data_finder(files[0], inputschema).data

    data_list = []
    for i in range(0, len(files)):
        try:
            data_list.append(data_finder(files[i], inputschema).get_data())
            msg = 'successfully loaded %s' % os.path.basename(files[i])
        except:
            msg = 'Cannot load data %s ' % files[i]

        print(msg)

    data = pd.concat(data_list). \
        reset_index(drop=True). \
        merge(pd.read_excel(join(rootdir, 'dates_cutoff.xlsx')),
              on='Subject', how='left')

    data.loc[

        (data['date'] >= data['Assessment B']) & \
        (data['date'] < data['Training start date'])
        ,

        'interval'] = 0

    data.loc[

        (data['date'] >= data['Training start date']) & \
        (data['date'] < data['1 month assessment'])
        ,

        'interval'] = 1

    print('Computing intervals')
    for i in list(range(1, 7)) + [9]:
        add = 1 if i <= 5 else 3
        print((i, i + add))

        data.loc[

            (data['date'] >= data[str(i) + ' month assessment']) & \
            (data['date'] <= data[str(i + add) + ' month assessment'])
            ,

            'interval'] = i + add
        print(('interval {} done'.format(i)))

    print("Computing means across interval")
    sum_cols = ['calories_burned', 'steps', 'distance', 'floors', 'min_sed', 'min_light', 'min_factive', 'min_vactive',
                'activity_calories']
    'calories_burned'

    data[sum_cols] = data[sum_cols].replace(0, np.nan)
    sum_data = data.pivot_table(values=sum_cols,
                                index=['Subject', 'interval'],
                                aggfunc='mean')

    output_filename = 'FITBIT' + '_' + datetime.today().strftime('%Y-%m-%d') + '.csv'
    output_raw = 'FITBITraw' + '_' + datetime.today().strftime('%Y-%m-%d') + '.csv'
    print(('Saving file {}'.format(output_filename)))
    sum_data.to_csv(join(outputdir, output_filename))
    data.to_csv(join(outputdir, output_raw))
