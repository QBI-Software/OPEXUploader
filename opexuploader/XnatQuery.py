
"""
TITLE: XnatQuery
AUTHOR: Alan Ho
"""

import sys
import re
import pandas as pd
import numpy as np
from os.path import join, expanduser
from os import getcwd
from functools import reduce

sys.path.append(getcwd())
from xnatconnect.XnatConnector import XnatConnector


class XnatQuery(XnatConnector):

    def __init__(self, listofexperiments, columns = None, criteria=None, **kwargs):
        XnatConnector.__init__(self, **kwargs)
        self.connect()

        if listofexperiments is None:
            listofexperiments = self.conn.inspect.datatypes('opex:')


        xnatcompiler = {}
        for experiment in listofexperiments:
            print(('Compiling {}'.format(experiment)))
            init = fetchData(connector=self,
                             experiment=experiment,
                             columns=columns,
                             criteria=criteria)

            init.connector.conn.disconnect()

            xnatcompiler[experiment] = {'data': init.data, 'fields': init.fields, 'ID': init.IDS}

        self.compiler = xnatcompiler
        dflist = [self.compiler[key]['data'] for key in list(self.compiler.keys())]
        self.data = reduce(lambda x, y: pd.merge(x, y, on=['Subject', 'interval', 'Exercise', 'Gender']), dflist)


class fetchData:

        def __init__(self, connector, experiment, columns=None, criteria=None):
            self.experiment = experiment
            self.columns = columns
            self.criteria = criteria
            self.connector = connector
            self.__get()
            self.__getIDS()

        def __get(self):
            fields = self.connector.conn.inspect.datatypes(self.experiment)
            fields = [f for f in fields if removeFields(f)]

            if self.columns is None:
                self.columns = ['xnat:subjectData/SUBJECT_LABEL',
                           'xnat:subjectData/SUB_GROUP',
                           'xnat:subjectData/GENDER_TEXT',
                           '{}/INTERVAL'.format(self.experiment),
                           '{}/AGE'.format(self.experiment)] + fields

            if self.criteria is None:
                self.criteria = [('xnat:subjectData/SUBJECT_ID', 'LIKE', '*'), 'AND']

            if self.experiment is None:
                self.experiment = 'xnat:subjectData'

            rename_cols = {
                'xnat_subjectdata_subject_label': 'Subject',
                'xnat_subjectdata_gender_text': 'Gender',
                'xnat_subjectdata_sub_group': 'Exercise'
            }

            subj = self.connector.conn.select(self.experiment, self.columns).where(self.criteria)

            if len(subj) > 0:
                df_subjects = pd.DataFrame(list(subj))
                df_subjects.rename(columns=rename_cols, inplace=True)

                self.fields = [col for col in df_subjects.columns if not bool(re.match('.*(age|interval|Gender|Exercise|Subject)', col))]

            self.data = df_subjects.convert_objects(convert_numeric=True)

        def __getIDS(self):

            self.IDS = self.data.set_index(['Subject', 'interval', 'Exercise', 'Gender']).\
                        dropna(how='all').\
                        reset_index().\
                        assign(ID = lambda x: x['Subject'].str.slice(0,4)).\
                        filter(items=['ID', 'interval'], axis=1)

        def __reshapeBloods(self):

            if 'prepost' in self.fields:
                bloodfields = [f for f in self.fields if not bool(re.match('.*(prepost)', f))]
                df = self.data.pivot_table(index='Subject', columns='prepost', values=bloodfields)
                df.columns = ['_'.join(col).strip() for col in df.columns.values]

                for b in bloodfields:
                    df[b + '_max'] = df[[b + "_post", b + "_pre"]].max(axis=1)
                    df[b + '_percent'] = (df[b + "_post"] - df[b + "_pre"])/df[b + "_pre"] * 100

                self.fields = df.columns
                self.data = df

            return self


def removeFields(field):

    remove_columns = ['COMMENTS',
                      'DATE',
                      'EXPT',
                      'INSERT_DATE',
                      'INSERT_USER',
                      'STATUS',
                      'SUBJECT_ID',
                      'PROJECT',
                      'SAMPLE_ID',
                      'SAMPLE_NUM',
                      'INTERVAL',
                      'AGE',
                      'SAMPLE_QUALITY',
                      'DATA_VALID']

    return not bool(re.match('.*({})'.format('|'.join(remove_columns)), field))


##################################

if __name__ == '__main__':

    home = expanduser("~")
    configfile = join(home, '.xnat.cfg')

    xnat = XnatQuery(listofexperiments=['opex:dexa'], configfile=configfile, sitename="opex")

    xnat.data.pivot_table(index=['Exercise','interval'], aggfunc=np.size)

    xnat.data.pivot_table(index=['interval'],columns='Exercise', aggfunc=np.size)
    null_columns = xnat.data.columns[xnat.data.isnull().any()]
    print((xnat.data[null_columns].isnull().sum()))

    xnat.data.groupby(['Exercise', 'interval']).isna().sum()
    xnat.data.pivot_table(index=['Exercise', 'interval'],
                          aggfunc=lambda x: x.isnull().sum())

    df = xnat.data.set_index(['Subject','Gender','Exercise', 'interval'])

    df[df.isnull().any(axis=1)].query('interval not in (3,9)')


    dflist = [xnat.compiler[key]['data'] for key in list(xnat.compiler.keys())]
    reduce(lambda x,y: pd.merge(x,y, on=['Subject', 'interval', 'Exercise', 'Gender']), dflist)