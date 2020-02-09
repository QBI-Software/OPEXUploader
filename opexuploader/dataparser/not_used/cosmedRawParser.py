"""
    Cosmed Raw Parser

    This parses the raw cosmed files and then uploads them into xnat

******LOOKS TO BE VERY INCOMPLETE ???*****
"""

import itertools
import os
import re
from datetime import datetime
from os.path import join, splitext

import pandas as pd




class schema_file:

    def __init__(self, file, schema_path):
        self.file = file
        self.headers = pd.read_csv(schema_path)['Variable']
        self.fields = pd.read_csv(schema_path)['Field']
        self.types = pd.read_csv(schema_path)['Type']
        self.subject = os.path.basename(os.path.dirname(self.file))



class cosmedRawParser(schema_file):

    def __init__(self, file, schema_path):
        schema_file.__init__(self, file, schema_path)
        base = os.path.split(self.file)[1]

        if self.info is None:
            self.info = {'prefix': 'COSR', 'xsitype': 'opex:cosmedraw'}

        self.subject = base[0:6]
        self.interval = int(filter(str.isdigit, [i for i in re.split('\_', base) if 'Month' in i][0]))
        self.seconds = [i for i in re.split('\_', base) if 'sec' in i][0]
        self.session = re.search('(?<=Month)(.*)',[i for i in re.split('\_', base) if 'Month' in i][0]).group()
        self.date = datetime.strptime(re.split('\_', splitext(base)[0])[-1], "%Y%m%d")


    def print_all(self):
        print self.file, self.subject, self.seconds, self.session, self.date

    def get_df(self, include_termination = False):

        """
        This processes the individual cosmed file by selecting only the columns starting with t to the end

        """
        df = pd.read_excel(self.file)

        index1 = df.columns.get_loc('t')
        index2 = df.shape[1]

        self.data = df.iloc[2:, index1:index2]
        self.data.rename(dict(zip(self.headers, self.fields)))
        # self.data.astype(dict(zip(self.fields, self.types)))
        self.data['Subject'] = self.subject
        self.data['interval'] = int(self.interval)
        self.data['session'] = self.session
        self.data['second'] = self.seconds
        self.data['session_date'] = self.date

        # load reasons for termination file
        termination = pd.read_excel(r'Q:\DATA\COSMEDdata\VO2 Checklists\Clinican request to stop tests.xlsx')
        termination.columns = ['Subject', 'session', 'term_reason']
        termination['Subject'] = termination['Subject'].str.replace(" ", "")
        termination['session'] = termination['session'].str.slice(2, 3)

        if include_termination == True:
            self.data = pd.merge(self.data,termination, on = ['Subject', 'session'], how = 'left')

        return self.data

    def check_session(self, rules_df=pd.DataFrame(None)):
        rules_col = ['AxA', 'AxB', 'AxC', 'AxD', 'AxE', 'AxF']

        if rules_df.empty:
            rules = pd.read_excel(r'Q:\DATA\COSMEDdata\VO2 Checklists\test_rules.xlsx', skiprows=1)
        else:
            rules = rules_df

        rules = rules[['ID'] + rules_col]
        rules['ID'] = rules['ID'].str.replace(" ", "")
        condition = [rule for rule in rules_col if self.session in rule[2:3]]

        if rules.ix[rules['ID'] == self.subject][condition].values == 'x':
            out = 'Bad'
        else:
            out = 'Good'

        return out

    def getxsd(self):
        xsd ={'MOT':'opex:cantabMOT',
            'PAL':'opex:cantabPAL',
            'SWM':'opex:cantabSWM',
            'ERT':'opex:cantabERT',
            'DMS':'opex:cantabDMS'
              }
        return xsd

def files_seconds(dir, second):
    return [os.path.join(dp, f) for dp, dn, fn in os.walk(join(dir, second)) for f in fn]

# ----------------------------
if __name__ == "__main__":


    inputdir = r'Q:\\DATA\\COSMEDdata'
    inputschema = r'Q:\\DATA\\COSMEDdata\cosmed_dict.csv'
    rules_col = ''  # No idea what this is
    # rules for deciding which files to process
    rules = pd.read_excel(join(inputdir, r'VO2 Checklists\test_rules.xlsx'), skiprows=1)[['ID'] + rules_col]

    # files to be processed within the inputdir
    files_list = list(itertools.chain.from_iterable([files_seconds(inputdir, sec) for sec in ['10sec', '30sec']]))
    files = [f for f in files_list if os.path.splitext(f)[1] == '.xlsx']

    files = files[1:500]

    # loop to process and then upload data!
    data_list = []
    print "Reading files in %s" % inputdir
    print "Compiling raw cosmed files***********************"
    for i in range(0, len(files)):

        if cosmedRawParser(files[i], inputschema).check_session(rules_df=rules) == 'Good':
            try:
                data_list.append(cosmedRawParser(files[i], inputschema).get_df(include_termination=True))
                print 'successfully loaded %s' % os.path.basename(files[i])

            except:
                print 'Cannot load data %s' % files[i]

        else:
            print "Bad session - ignoring %s " % files[i]

    data = pd.concat(data_list).reset_index(drop=True)
    print """FINISHED COMPILING *****************************
    
    log available in directory Q:/Users
    """
    print "Starting Upload ********************************"




#
#
# data_list[100]
# len(data_list)
# files.index('')
#
#
# len(data_list)
#
# for f in files:
#     print f + " :" + str(len(pd.read_excel(f).columns))
#
# df1 = cosmedRawParser(r'Q:\\DATA\\COSMEDdata\10sec\1005CB_0MonthA_10sec_20170130.xlsx', inputschema).get_df()
# df2 = cosmedRawParser(r'Q:\\DATA\\COSMEDdata\10sec\1057PW_9MonthE_10sec_20180212.xlsx', inputschema).get_df()
#
#
# pd.concat([df1, df2])
# list(set(df1.columns) - set(df1.columns))
# s.difference(t)
# df2.columns.difference(df1.columns)
# data
# files[len(data_list) + 1]
# len(data_list)
#
# [len(d.columns) for d in data_list]
#
# data['Subject'].unique()
# df2.columns
# df['week'][(df['date'] >= weeks[i]) & (df['date'] < weeks[i + 1])] = group
#
# data[(data['Subject'] == '1005CB') & (data['session'] == 'A')].shape
#
#
# data.to_csv(join(inputdir, 'cosmedrawtest.csv'))
#
# data.ix[data['session'] == 'A']
#
# check = data[(data['Subject'] == '1005CB') & (data['session'] == 'A')]
#
# check.to_csv(join(inputdir, 'test1005.csv'))
# del check