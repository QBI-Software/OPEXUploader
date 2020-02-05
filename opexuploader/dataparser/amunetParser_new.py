
"""
TITLE  - Virtual Water Maze Parser
@author Alan Ho, QBI 2018
"""

import sys
import os
import sys
import re
import zipfile
import pandas as pd
import numpy as np
import argparse
import logging
import csv
from os.path import join, splitext
from datetime import datetime
import xml.etree.ElementTree as ET

sys.path.append('C:/Users/uqaho4/PycharmProjects/OPEXUploader')
from opexuploader.dataparser.abstract.DataParser import DataParser

# logging.basicConfig(filename='amunet.log',level=logging.DEBUG)

class amunetParser(DataParser):

    def __init__(self, pathtofile,pathtoerrors=None, *args):
        DataParser.__init__(self, *args)
        self.fields = None
        self.datafile = None
        self.info = None

        self.resource_dir = None

        # logging.info('Initalising: ' + pathtofile)
        self.pathtofile = pathtofile
        self.pathtoerrors = pathtoerrors
        if pathtoerrors is not None:
            self.errors = pd.read_csv(pathtoerrors)

        self.get_interval()
        # logging.info('Parsing xml tree')
        self.get_tree()
        self.get_date()
        self.root = self.tree.getroot()
        self.type = self.root.attrib['name']
        self.subject_details()
        self.details['Name'] = correct_subjects(self.details['Name'])
        self.get_experiments()
        # logging.info('Formatting data')
        self.get_data()
        self.sortSubjects()
        self.get_comments()
        # logging.info('Complete')

    def get_tree(self):

        if splitext(self.pathtofile)[-1] == '.zip':
            zip_ref = zipfile.ZipFile(self.pathtofile, 'r')
            for filename in zip_ref.namelist():
                if splitext(filename)[-1] == '.xml'and filter_xml(filename) == filter_xml(self.pathtofile):
                    file = zip_ref.open(filename)
                    self.tree = ET.parse(file)
                    zip_ref.close()

        elif splitext(self.pathtofile)[-1] == '.xml':
                self.tree = ET.parse(filetopath)

        else:
            print('specify proper filepath (xml or zip file)')

        return self.tree

    def get_date(self):
        string = os.path.basename(self.pathtofile)
        date_string = re.findall('(?<=_)\\d*(?=.zip)', string)[0]

        try:
            self.date = datetime.strptime(date_string, "%Y%m%d").strftime("%d-%m-%Y")
        except:
            self.date = datetime.strptime(date_string, "%d%m%Y").strftime("%d-%m-%Y")

    def subject_details(self):
        details = {}
        for child in self.root.findall('./Subject')[0]:
            name = child.tag
            details[name] = child.text

        self.details = details

    def get_experiments(self):
        for actor in self.root.findall('Experiments'):
            exp = actor.findall('Experiment')
            exp_name = [e.attrib['name'] for e in exp]

        self.experiments = exp_name
        return self.experiments

    def get_data(self):
        exp_data = {}
        # logging.info('Compiling: ' + str(self.experiments))
        for exp in self.experiments:
            exp_path = ".//*[@name='{}']/Phases/".format(exp)
            temp = self.root.findall(exp_path)
            temp_data = dict(list(zip(list(range(1, len(temp) + 1)), [self.get_elements(t, remove="MousePath") for t in temp])))
            exp_data[exp] = pd.DataFrame.from_dict(temp_data, orient='index')
            exp_data[exp].index.names = ['trials']

        df = pd.concat(exp_data, axis=0)
        df.replace('NaN', '', regex=True, inplace=True)
        df = df.apply(pd.to_numeric).reset_index()
        df['Subject'] = self.details['Name']
        df['Visit'] = self.details['Visit']
        df['Type'] = self.type
        df['interval'] = int(self.interval)
        df['date'] = self.date
        df['experiments'] = df['level_0'].apply(lambda x: change_explabels(x))
        df = df.set_index(['Subject', 'Type', 'Visit', 'interval', 'date', 'experiments', 'trials'])
        df.drop(columns='level_0', inplace=True)
        self.data = df



        # # General Filter
        #
        # if self.pathtoerrors is not None:
        #     df = filter_by_errors(df=df, errors=self.errors)
        #     df = df.set_index(['Subject', 'Type', 'Visit', 'interval', 'date', 'experiments', 'trials'])
        #     df = df[~(df == 0).all(axis=1)]. \
        #         query("PathDifference > 0 | TotalError > 0")
        #
        #
        #
        # df.drop(columns='level_0', inplace=True)
        #
        # df = df.set_index(['Subject', 'Type', 'Visit', 'interval', 'date','experiments', 'trials'])
        #
        # # filter out rows with all zeroes
        # df = df[~(df == 0).all(axis=1)].\
        #         query("MinimalDistanceFromGoal > 0 & trials > 1")
        #
        # # filter out rows with partial zeros (except miniminal distance)
        # columns_filter = [
        #     "AngularDeviation",
        #     "StartGoalDistance",
        #     "DistanceDeviation",
        #     "DistanceFromStart",
        #     "TotalError",
        #     "PathDifference",
        #     "PathLength",
        #     "Duration",
        #     "AngularDeviation"
        # ]
        # df = df[(df[columns_filter] != 0).all(axis=1)]
        #
        # if self.pathtoerrors is not None:
        #     df = filter_by_errors(df=df, errors=self.errors)
        #     df = df.set_index(['Subject', 'Type', 'Visit', 'interval', 'date', 'experiments', 'trials'])

        # self.data = df

    def mapData(self):
        agg_dict = {'Duration': [np.sum, np.mean],
                    'AngularDeviation': np.mean,
                    'PathLength': np.mean,
                    'PathDifference': np.mean,
                    'TotalError': [np.mean, np.std, compute_se],
                    'DistanceDeviation': np.mean}
        sum_results = self.data.reset_index().pivot_table(index=['experiments'],
                                                   values=list(agg_dict.keys()),
                                                   aggfunc=agg_dict)


        xsd = self.getxsd()

        mandata = {
            # xsd + '/date': str(self.date),
            xsd + '/interval': str(self.interval),
            xsd + '/sample_id': '',  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': ''
        }


        if self.type == 'Amunet 1':
            motdata = {
                xsd + '/AEV_comments': str(self.lexical['AlloEgo Virtual']),
                xsd + '/AEV_tot_duration': str(sum_results.loc['AlloEgo Virtual', ('Duration', 'sum')]),
                xsd + '/AEV_mean_duration': str(sum_results.loc['AlloEgo Virtual', ('Duration', 'mean')]),
                xsd + '/AEV_mean_angdev': str(sum_results.loc['AlloEgo Virtual', ('AngularDeviation', 'mean')]),
                xsd + '/AEV_mean_pathdiff': str(sum_results.loc['AlloEgo Virtual', ('PathDifference', 'mean')]),
                xsd + '/AEV_mean_toterror': str(sum_results.loc['AlloEgo Virtual', ('TotalError', 'mean')]),
                xsd + '/AEV_mean_distdev': str(sum_results.loc['AlloEgo Virtual', ('DistanceDeviation', 'mean')]),
                xsd + '/AEV_std_toterror': str(sum_results.loc['AlloEgo Virtual', ('TotalError', 'std')]),
                xsd + '/AEV_se_toterror': str(sum_results.loc['AlloEgo Virtual', ('TotalError', 'compute_se')]),
                xsd + '/AEV_mean_pathlength': str(sum_results.loc['AlloEgo Virtual', ('PathLength', 'mean')]),

                xsd + '/EV_comments': str(self.lexical['Ego Virtual']),
                xsd + "/EV_tot_duration": str(sum_results.loc['Ego Virtual', ('Duration', 'sum')]),
                xsd + "/EV_mean_duration": str(sum_results.loc['Ego Virtual', ('Duration', 'mean')]),
                xsd + "/EV_mean_angdev": str(sum_results.loc['Ego Virtual', ('AngularDeviation', 'mean')]),
                xsd + "/EV_mean_pathdiff": str(sum_results.loc['Ego Virtual', ('PathDifference', 'mean')]),
                xsd + "/EV_mean_toterror": str(sum_results.loc['Ego Virtual', ('TotalError', 'mean')]),
                xsd + "/EV_mean_distdev": str(sum_results.loc['Ego Virtual', ('DistanceDeviation', 'mean')]),
                xsd + "/EV_std_toterror": str(sum_results.loc['Ego Virtual', ('TotalError', 'std')]),
                xsd + "/EV_se_toterror": str(sum_results.loc['Ego Virtual', ('TotalError', 'compute_se')]),
                xsd + '/EV_mean_pathlength': str(sum_results.loc['Ego Virtual', ('PathLength', 'mean')]),

                xsd + '/AV_comments': str(self.lexical['Allo Virtual']),
                xsd + "/AV_mean_duration": str(sum_results.loc['Allo Virtual', ('Duration', 'mean')]),
                xsd + "/AV_mean_angdev": str(sum_results.loc['Allo Virtual', ('AngularDeviation', 'mean')]),
                xsd + "/AV_mean_pathdiff": str(sum_results.loc['Allo Virtual', ('PathDifference', 'mean')]),
                xsd + "/AV_mean_toterror": str(sum_results.loc['Allo Virtual', ('TotalError', 'mean')]),
                xsd + "/AV_mean_distdev": str(sum_results.loc['Allo Virtual', ('DistanceDeviation', 'mean')]),
                xsd + "/AV_std_toterror": str(sum_results.loc['Allo Virtual', ('TotalError', 'std')]),
                xsd + "/AV_se_toterror": str(sum_results.loc['Allo Virtual', ('TotalError', 'compute_se')]),
                xsd + '/AV_mean_pathlength': str(sum_results.loc['Allo Virtual', ('PathLength', 'mean')]),

                xsd + '/DV_comments': str(self.lexical['Delayed Virtual']),
                xsd + "/DV_mean_duration": str(sum_results.loc['Delayed Virtual', ('Duration', 'mean')]),
                xsd + "/DV_mean_angdev": str(sum_results.loc['Delayed Virtual', ('AngularDeviation', 'mean')]),
                xsd + "/DV_mean_pathdiff": str(sum_results.loc['Delayed Virtual', ('PathDifference', 'mean')]),
                xsd + "/DV_mean_toterror": str(sum_results.loc['Delayed Virtual', ('TotalError', 'mean')]),
                xsd + "/DV_mean_distdev": str(sum_results.loc['Delayed Virtual', ('DistanceDeviation', 'mean')]),
                xsd + "/DV_std_toterror": str(sum_results.loc['Delayed Virtual', ('TotalError', 'std')]),
                xsd + "/DV_se_toterror": str(sum_results.loc['Delayed Virtual', ('TotalError', 'compute_se')]),
                xsd + '/DV_mean_pathlength': str(sum_results.loc['Delayed Virtual', ('PathLength', 'mean')])
            }

        elif self.type == 'Amunet 2':
            motdata = {
                xsd + '/SCS_comments': str(self.lexical['Simple navigation - Cued Static']),
                xsd + '/SCS_tot_duration': str(sum_results.loc['Cued Static', ('Duration', 'sum')]),
                xsd + '/SCS_mean_duration': str(sum_results.loc['Cued Static', ('Duration', 'mean')]),
                xsd + '/SCS_mean_angdev': str(sum_results.loc['Cued Static', ('AngularDeviation', 'mean')]),
                xsd + '/SCS_mean_pathdiff': str(sum_results.loc['Cued Static', ('PathDifference', 'mean')]),
                xsd + '/SCS_mean_toterror': str(sum_results.loc['Cued Static', ('TotalError', 'mean')]),
                xsd + '/SCS_mean_distdev': str(sum_results.loc['Cued Static', ('DistanceDeviation', 'mean')]),
                xsd + '/SCS_std_toterror': str(sum_results.loc['Cued Static', ('TotalError', 'std')]),
                xsd + '/SCS_se_toterror': str(sum_results.loc['Cued Static', ('TotalError', 'compute_se')]),
                xsd + '/SCS_mean_pathlength': str(sum_results.loc['Cued Static', ('PathLength', 'mean')]),

                xsd + '/SCD_comments': str(self.lexical['Simple navigation - Cued Dynamic']),
                xsd + '/SCD_tot_duration': str(sum_results.loc['Cued Dynamic', ('Duration', 'sum')]),
                xsd + '/SCD_mean_duration': str(sum_results.loc['Cued Dynamic', ('Duration', 'mean')]),
                xsd + '/SCD_mean_angdev': str(sum_results.loc['Cued Dynamic', ('AngularDeviation', 'mean')]),
                xsd + '/SCD_mean_pathdiff': str(sum_results.loc['Cued Dynamic', ('PathDifference', 'mean')]),
                xsd + '/SCD_mean_toterror': str(sum_results.loc['Cued Dynamic', ('TotalError', 'mean')]),
                xsd + '/SCD_mean_distdev': str(sum_results.loc['Cued Dynamic', ('DistanceDeviation', 'mean')]),
                xsd + '/SCD_std_toterror': str(sum_results.loc['Cued Dynamic', ('TotalError', 'std')]),
                xsd + '/SCD_se_toterror': str(sum_results.loc['Cued Dynamic', ('TotalError', 'compute_se')]),
                xsd + '/SCD_mean_pathlength': str(sum_results.loc['Cued Dynamic', ('PathLength', 'mean')]),

                xsd + '/SES_comments': str(self.lexical['Simple navigation - Ego Static']),
                xsd + "/SES_tot_duration": str(sum_results.loc['Ego Static', ('Duration', 'sum')]),
                xsd + "/SES_mean_duration": str(sum_results.loc['Ego Static', ('Duration', 'mean')]),
                xsd + "/SES_mean_angdev": str(sum_results.loc['Ego Static', ('AngularDeviation', 'mean')]),
                xsd + "/SES_mean_pathdiff": str(sum_results.loc['Ego Static', ('PathDifference', 'mean')]),
                xsd + "/SES_mean_toterror": str(sum_results.loc['Ego Static', ('TotalError', 'mean')]),
                xsd + "/SES_mean_distdev": str(sum_results.loc['Ego Static', ('DistanceDeviation', 'mean')]),
                xsd + "/SES_std_toterror": str(sum_results.loc['Ego Static', ('TotalError', 'std')]),
                xsd + "/SES_se_toterror": str(sum_results.loc['Ego Static', ('TotalError', 'compute_se')]),
                xsd + '/SES_mean_pathlength': str(sum_results.loc['Ego Static', ('PathLength', 'mean')]),

                xsd + '/SAS_comments': str(self.lexical['Simple navigation - Allo Static']),
                xsd + "/SAS_tot_duration": str(sum_results.loc['Allo Static', ('Duration', 'sum')]),
                xsd + "/SAS_mean_duration": str(sum_results.loc['Allo Static', ('Duration', 'mean')]),
                xsd + "/SAS_mean_angdev": str(sum_results.loc['Allo Static', ('AngularDeviation', 'mean')]),
                xsd + "/SAS_mean_pathdiff": str(sum_results.loc['Allo Static', ('PathDifference', 'mean')]),
                xsd + "/SAS_mean_toterror": str(sum_results.loc['Allo Static', ('TotalError', 'mean')]),
                xsd + "/SAS_mean_distdev": str(sum_results.loc['Allo Static', ('DistanceDeviation', 'mean')]),
                xsd + "/SAS_std_toterror": str(sum_results.loc['Allo Static', ('TotalError', 'std')]),
                xsd + "/SAS_se_toterror": str(sum_results.loc['Allo Static', ('TotalError', 'compute_se')]),
                xsd + "/SAS_tot_duration": str(sum_results.loc['Allo Static', ('Duration', 'sum')]),
                xsd + '/SAS_mean_pathlength': str(sum_results.loc['Allo Static', ('PathLength', 'mean')]),

                xsd + '/SAD_comments': str(self.lexical['Simple navigation - Allo Dynamic']),
                xsd + "/SAD_mean_duration": str(sum_results.loc['Allo Dynamic', ('Duration', 'mean')]),
                xsd + "/SAD_mean_angdev": str(sum_results.loc['Allo Dynamic', ('AngularDeviation', 'mean')]),
                xsd + "/SAD_mean_pathdiff": str(sum_results.loc['Allo Dynamic', ('PathDifference', 'mean')]),
                xsd + "/SAD_mean_toterror": str(sum_results.loc['Allo Dynamic', ('TotalError', 'mean')]),
                xsd + "/SAD_mean_distdev": str(sum_results.loc['Allo Dynamic', ('DistanceDeviation', 'mean')]),
                xsd + "/SAD_std_toterror": str(sum_results.loc['Allo Dynamic', ('TotalError', 'std')]),
                xsd + "/SAD_se_toterror": str(sum_results.loc['Allo Dynamic', ('TotalError', 'compute_se')]),
                xsd + '/SAD_mean_pathlength': str(sum_results.loc['Allo Dynamic', ('PathLength', 'mean')]),

                xsd + '/SED_comments': str(self.lexical['Simple navigation - Ego Dynamic']),
                xsd + "/SED_mean_duration": str(sum_results.loc['Ego Dynamic', ('Duration', 'mean')]),
                xsd + "/SED_mean_angdev": str(sum_results.loc['Ego Dynamic', ('AngularDeviation', 'mean')]),
                xsd + "/SED_mean_pathdiff": str(sum_results.loc['Ego Dynamic', ('PathDifference', 'mean')]),
                xsd + "/SED_mean_toterror": str(sum_results.loc['Ego Dynamic', ('TotalError', 'mean')]),
                xsd + "/SED_mean_distdev": str(sum_results.loc['Ego Dynamic', ('DistanceDeviation', 'mean')]),
                xsd + "/SED_std_toterror": str(sum_results.loc['Ego Dynamic', ('TotalError', 'std')]),
                xsd + "/SED_se_toterror": str(sum_results.loc['Ego Dynamic', ('TotalError', 'compute_se')]),
                xsd + '/SED_mean_pathlength': str(sum_results.loc['Ego Dynamic', ('PathLength', 'mean')])
            }

        return mandata, motdata

    def get_comments(self):
        self.lexical = {}
        for exp in self.experiments:
            exp_path = ".//*[@name='{}']/LexicalRating".format(exp)
            self.lexical[exp] = self.root.findall(exp_path)[0].text

    def get_interval(self):
        string = os.path.dirname(self.pathtofile)
        self.interval = re.findall('\\d*(?=M)', os.path.basename(string))[0]

    def getSampleid(self, sd):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'AM' + '_' + sd + '_' + str(self.interval) + 'M'
        return id

    def sortSubjects(self, subjectfield='ID'):
        self.subjects = dict()
        ids = self.details['Name']
        for sid in [ids]:
            if len(str(sid)) == 6:
                # sidkey = self.__checkSID(sid)
                self.subjects[sid] = self.details['Name']
        msg = 'Subjects loaded=%d' % len(self.subjects) + str(self.subjects)
        print(msg)

    def _loadData(self):
        pass

    # you need to fix this function !!!!!!!!!!
    def get_elements(self, object, index=0, remove=None):

        if isinstance(object, str):
            details = {}
            for child in self.root.findall(object)[index]:
                name = child.tag
                details[name] = child.text

        else:
            details = {}
            for child in object:
                name = child.tag
                details[name] = child.text

        if remove is not None:
            del details[remove]

        return details

    def getxsd(self):
        return 'opex:amunetall'

    def getSubjectData(self,sd):
        """
        Extract subject data from input data
        :param sd:
        :return:
        """
        skwargs = {}
        # if self.subjects is not None:
        #     # dob = self.formatDobNumber(self.details['DateOfBirth'])
        #     gender = str(self.details['Sex'])[0]
        #     # skwargs = {'dob': dob}
        #     if gender in ['F', 'M']:
        #         skwargs['gender'] = gender

        return skwargs


def change_explabels(string):
    try:
        label = re.split('-', string)[1].strip()

    except:
        label = string

    return label

def compute_se(series):
    return np.std(series, ddof=1)/np.sqrt(len(series))

def filter_xml(filetopath):
    sub = re.findall('\\d{4}', os.path.basename(filetopath))[0]
    return sub

def lookup_errors(errorfilepath = 'Q:\\DATA\\DATA ENTRY\\hMWM results\\hMWM_new_template.xlsx'):
    errors_list = []
    xl = pd.ExcelFile(errorfilepath)
    for name in xl.sheet_names[0:3]:
        errors_list.append(xl.parse(name))

    errors_df = pd.concat(errors_list)
    errors_df['trials'] = errors_df['Errors'].apply(lambda x: re.findall('\\d*(?=/)', x)[0])
    errors_df['experiments'] = errors_df['Errors'].apply(lambda x: re.findall('.+?(?=\\d)', x)[0])

    return errors_df[['Subject', 'interval', 'experiments', 'trials']]

def correct_subjects(subject, pathtosubjectfile='C:/Users/uqaho4/PycharmProjects/OPEXUploader/P1_subjectlist.csv', idfield='ID'):
    correct_subs = pd.read_csv(pathtosubjectfile)
    subj_no = re.findall('\\d+',subject)[0]

    bool_filt = correct_subs[idfield].str.contains(subj_no)
    return correct_subs[idfield][bool_filt].values[0]

def filter_by_errors(df, errors):
    errors['marker'] = 1
    joined = pd.merge(df.reset_index(), errors, how='left')

    return joined[pd.isnull(joined['marker'])][df.reset_index().columns]


# pathtofile = r'Q:\DATA\DATA ENTRY\hMWM results\1. 0M_Baseline\1177VM_Amunet 2_0Month_20180321.zip'
# dp = amunetParser(pathtofile, errors_path)
#
# dp.data.\
#     query("MinimalDistanceFromGoal != 0 & trials > 1")
########################################################################################################

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='Parse Water Maze (Amunet) Files (from zip or xml)',
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing files',
                        default="C:\\Users\\uqaho4\\Desktop\\hMWM")

    parser.add_argument('--outdir', action='store', help='Path / filename of raw data',
                        default="C:\\Users\\uqaho4\\Desktop\\hMWM\\Batches")

    parser.add_argument('--filter', action='store', help='Filter Type',
                        default="NoFilter")

    args = parser.parse_args()

    root_dir = args.filedir
    interval_dir = ['1. 0M_Baseline','2. 3M_Interim','3. 6M_Post','4. 9M_Maintenance','5. 12M_Final']
    # interval_dir = ['5. 12M_Final']
    # errors_path = "Q:\\DATA\\DATA ENTRY\\hMWM results\\errors_template.csv"
    errors_path = "C:\\Users\\uqaho4\\Desktop\\hMWM\\errors_template.csv"


    output_filename = "batch_{}_{}.csv".format(args.filter, datetime.today().strftime("%Y-%m-%d"))
    output_file = join(args.outdir, output_filename)
    # output_file = join(os.path.dirname(root_dir), 'completetest.csv')
    # test = '1015HB_AMUNET 1_0Month_20170214.zip'

    correct_errors = input('Correct for errors? ')

    single_file = input('Process single file? [y/n]')
    if 'y' in single_file:
        pathtofile= input("Specify path to file ")
        if 'y' in correct_errors:
            dp = amunetParser(pathtofile, errors_path)
        else:
            dp = amunetParser(pathtofile)

        save_file = input('Save to file? [y/n]')
        if 'y' in save_file:
            output_file = input('Where? ')
            dp.data.to_csv(output_file)
        elif 'n' in save_file:
            for sd in dp.subjects:
                print(('*****SubjectID:', sd))
                sd = str(sd)  # prevent unicode
                sampleid = dp.getSampleid(sd)
                print((dp.data))
                print(sampleid)

                (mandata, data) = dp.mapData()
                print(mandata)
                print(data)

# "Q:\DATA\DATA ENTRY\hMWM results\4. 9M_Maintenance"
    # "Q:\\DATA\\DATA ENTRY\\hMWM results\\1. 0M_Baseline\\1054MR_Amunet1_12Month_20180503.zip"
    else:
        msg = """***** AMUNET PARSER ****** \n Run on {} """.format(datetime.today())
        print(msg)
        # logging.info(msg)
        for i in interval_dir:
            path = join(root_dir, i)
            msg = '############# FILE DIRECTORY : {} #############'.format(path)
            # logging.info(msg)
            files = [f for f in os.listdir(path) if splitext(f)[-1] == '.zip' or splitext(f)[-1] == '.xml']

            if not os.path.isfile(output_file):
                with open(output_file, 'w'):
                    pass

            for f2 in files:
                msg = "------------------------- STARTING: " + f2 + " -----------------------------"
                # logging.info(msg)
                print(msg)
                filetopath = join(path, f2)
                try:
                    if 'n' in correct_errors:
                        dp = amunetParser(filetopath)
                    elif 'y':
                        dp = amunetParser(filetopath, errors_path)

                    print((dp.data))

                    # (mandata, data) = dp.mapData()
                    # print(mandata,data)

                    with open(output_file) as csvfile:
                        sniffer = csv.Sniffer()
                        try:
                            has_header = sniffer.has_header(csvfile.read(2048))
                        except:
                            has_header = False

                    dp.data.to_csv(output_file, mode='a', header=not has_header)

                except IOError as e:
                    msg = 'ERROR:' + str(e)
                    print(msg)
                    logging.error(msg)
                except ValueError as e:
                    msg = 'ValueError:' + str(e)
                    print(msg)
                    logging.error(msg)
                except Exception as e:
                    print(e)
                    msg = 'Exception:' + str(e)
                    print(msg)
                    logging.error(msg)
