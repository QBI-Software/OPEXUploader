
import pandas as pd
import os
from os import listdir
from os.path import join
import re
import sys
import argparse

from os.path import basename, dirname

sys.path.append(os.getcwd())
from opexuploader.dataparser.MRIParserJunjie import JunjieParser


class fMRITaskParser(JunjieParser):

    def __init__(self, inputdir):
        super(JunjieParser, self).__init__()

        self.inputdir = inputdir
        self.etype = basename(self.inputdir)
        self.fields = ['load', 'condition', 'left_PHC', 'left_CA23', 'left_CA1', 'left_SUB', 'left_DG',
                       'right_PHC', 'right_CA23', 'right_CA1', 'right_SUB', 'right_DG']
        self.getData()
        self.sortSubjects('Subject')


    def getData(self):
        files = os.listdir(self.inputdir)

        datalist = {}

        for file in files:
            side = re.search('(right|left)', file).group(1)
            interval = re.search('(bl|m6|m12)', file).group(1)
            if interval == 'm12': interval = '12'
            if interval == 'm6': interval = '6'
            if interval == 'bl': interval = '0'

            taskload = re.search('(Loc|Obj|Bind)\\d{0,1}', file).group(0)
            if taskload == 'Obj': taskload = 'Obj35'
            if taskload == 'Loc': taskload = 'Loc35'
            if taskload == 'Bind': taskload = 'Bind35'
            data = pd.read_csv(join(self.inputdir, file))
            data['interval'] = interval
            data['taskload'] = taskload
            fields = ['SUB', 'CA1', 'CA23', 'DG', 'PHC']
            newfields = dict(list(zip(fields, [side + '_' + f for f in fields])))


            data.rename(columns=newfields, inplace=True)

            datalist[taskload + '_' + side + '_' + interval] = data

        leftdf = pd.concat([datalist[key] for key in list(datalist.keys())
                            if bool(re.search('left', key))])

        rightdf = pd.concat([datalist[key] for key in list(datalist.keys())
                             if bool(re.search('right', key))])

        self.data = pd.merge(rightdf, leftdf,
                             on=['Subject', 'interval', 'taskload'], how='outer')

        self.data[['condition', 'load']] = self.data['taskload']. \
                                                    str.extract('([A-Za-z]+)(\d+\.?\d*)', expand=True)


    def getxsd(self):

        xsd = {
            'taskret': 'opex:fmritaskret',
            'taskencode': 'opex:fmritaskencode'
        }

        return xsd[self.etype]

    def getSampleid(self, sd, row):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = self.etype.upper() + '_' + sd + '_' + str(row['interval'])+'M' + str(row['condition']) + str(row['load'])
        return id


def check_uniquecols(inputdir):
    datalist, fields = {}, {}
    for file in listdir(inputdir):
        filepath = join(inputdir, file)
        data = pd.read_csv(filepath)
        datalist[file] = data
        fields[file] = list(data.columns)

    # check if columns are unique
    unique_data = [list(x) for x in set(tuple(x)
                                        for x in list(fields.values()))]


    return unique_data

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="MRIparser(Junjie)",
                                     description="""\
                                     Parses MRI data from Junjie's data
                                     """)
    parser.add_argument('--inputdir', action='store',
                        default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\fmri\\task_output")
    parser.add_argument('--outputdir', action='store')



    args = parser.parse_args()

    inputdir = args.inputdir

    dp = fMRITaskParser(inputdir)

    if args.outputdir is not None:
        dp.data.\
            set_index(['Subject', 'interval']).\
            to_csv(args.outputdir)

    # for sd in dp.subjects:
    #     print('*****SubjectID:', sd)
    #     for i, row in dp.subjects[sd].iterrows():
    #         sampleid = dp.getSampleid(sd, row)
    #         (mandata, data) = dp.mapData(row, i)
    #         print(mandata)
    #         print(data)

