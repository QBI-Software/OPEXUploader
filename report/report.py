# -*- coding: utf-8 -*-
"""
Utility script: OPEXReport

run from console/terminal with (example):
>python OPEXReport.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
import logging
from datetime import datetime
from os.path import expanduser, join, abspath, dirname
from os import access, R_OK, mkdir
from collections import OrderedDict
import numpy as np
import pandas
import xlsxwriter
import plotly.plotly as py
import plotly.graph_objs as go
from plotly import tools
from plotly import offline
#import cufflinks as cf


class OPEXReport(object):
    def __init__(self, subjects=None, csvfile=None):
        """
        List of subjects from XNAT as collection
        :param subjects:
        :param csvfile: spreadsheet export from OPEX subjects tab (with counts)
        """
        self.subjects = subjects
        self.csvfile = csvfile
        self.subjectids = None
        self.data = None
        self.minmth = 0
        self.maxmth = 12
        self.cache = csvfile
        self.opex = self.__loadopexfile()
        self.xnat = None
        self.__loaddata()

    def __loaddata(self):
        if self.csvfile is not None:
            self.data = pandas.read_csv(self.csvfile)
        if self.subjects is not None:
            if isinstance(self.subjects, pandas.DataFrame):
                self.subjectids = self.subjects['subject_label']
            else:
                self.subjectids = [s.label() for s in self.subjects]
            print "Subjects loaded from database"
        elif self.data is not None and 'Subject' in self.data:
            self.subjectids = self.data.Subject.unique()
            print "Subject IDs loaded from file"

    def __loadopexfile(self):
        """
        Load experiment info from opex.csv
        :return:
        """
        try:
            self.resource_dir = self.__findResourcesdir()
            opexfile = join(self.resource_dir, 'opex.csv')
            opex = pandas.read_csv(opexfile)
            msg = 'OPEX Resources loaded: %s from %s' % (not opex.empty, opexfile)
            logging.info(msg)
            return opex
        except Exception as e:
            msg = 'OPEX Resources NOT loaded: %s' % (e.args[0])
            logging.error(msg)
            raise IOError(e)

    def __findResourcesdir(self):
        resource_dir = glob.glob(join(dirname(__file__), "resources"))
        middir = ".."
        ctr = 1
        while len(resource_dir) <= 0 and ctr < 5:
            resource_dir = glob.glob(join(dirname(__file__), middir, "resources"))
            middir = join(middir, "..")
            ctr += 1
        return abspath(resource_dir[0])

    def getParticipants(self):
        """
        Get Number of participants grouped by Group and Gender
        :return:
        """
        if self.data is not None:
            groups = self.data[['Group', 'M/F']]
            groups.columns = ['group', 'gender']
        elif isinstance(self.subjects, pandas.DataFrame):
            groups = self.subjects[['sub_group', 'gender_text']]
            groups.rename(columns={'sub_group': 'group', 'gender_text': 'gender'}, inplace=True)
        else:
            groups = pandas.DataFrame([(s.attrs.get('group'), s.attrs.get('gender')) for s in self.subjects],
                                      columns=['group', 'gender'])
        # Set up frequency histogram
        df = groups.groupby('group').count()
        if 'male' in groups.gender.unique():
            df_male = groups.groupby(['gender']).get_group('male')
            df_female = groups.groupby(['gender']).get_group('female')
        else:
            df_male = groups.groupby(['gender']).get_group('M')
            df_female = groups.groupby(['gender']).get_group('F')
        df['Male'] = df_male.groupby('group').count()
        df['Female'] = df_female.groupby('group').count()
        df = df.rename(columns={'gender': 'All'})
        dg = df['All']._construct_axes_dict()  # workaround
        df['Group'] = dg['index']
        df.replace(to_replace=np.nan, value=0, inplace=True)
        return df

    def getExptCollection(self, projectcode):
        """
        Generate Frequency histogram for expts collected
        :param csvfile:
        :return: sorted counts of each expt per participant
        """
        df = None
        if self.data is None:
            self.data = self.getExptCounts(projectcode)
        # Area chart or Stacked Bar Chart or Histogram
        groups = self.data
        # replace NaN with 0
        groups.fillna(0, inplace=True)
        # exclude withdrawn
        df = groups[groups.Group != 'withdrawn']
        # sort by largest number expts
        if 'MONTH' in df:
            df = df.sort_values('MONTH', ascending=True)
        else:
            df = df.sort_values('CANTAB DMS', ascending=True)
        # plot - exclude Subject, m/f,hand,yob
        cols = ['Group', 'Subject'] + list(self.opex['Expt'])
        cols_present = [h for h in cols if h in df.columns]
        df = df[cols_present]

        return df

    def processCounts(self, subj, q):
        """
        Process counts via multiprocessing
        :param subj:
        :return:
        """
        result = []
        if subj is not None:
            etypes = list(self.opex['xsitype'])  # self._expt_types()
            result = [subj.attrs.get('group'), subj.label(), subj.attrs.get('gender')]
            counts = self.xnat.getExptCounts(subj)
            for expt in list(self.opex['Expt']):
                etype = etypes[expt]
                if (etype in counts):
                    result.append(counts[etype])
                else:
                    result.append(0)

            result.append(self.getMONTH(counts['firstvisit']))
            q[subj.label()] = result
            # print result
        # print "Counts:", len(self.counts)
        return result

    def getExptCounts(self, projectcode):
        dfsubjects = None
        if self.xnat is not None:
            df_counts = self.getOPEXExpts(projectcode)
            # Get first visit as starting point in study
            v0 = df_counts.filter(regex="_visit", axis=1)
            v = v0.replace(['', np.nan], 'ZZZZZZZ')
            df_counts['first_visit'] = v.min(axis=1, skipna=True)
            df_counts.replace([np.inf, -np.inf, np.nan, 'ZZZZZZZ'], 0, inplace=True)
            dfsubjects = self.formatCounts(df_counts)
            self.data = dfsubjects

        return dfsubjects

    def getOPEXExpts(self, projectcode, headers=None):
        """
        Get Expt data to parse
        :return:
        """
        etypes = sorted(self.xnat.conn.inspect.datatypes())
        df_subjects = self.xnat.getSubjectsDataframe(projectcode)
        # Cannot load all at once nor can get count directly so loop through each prefix and compile counts
        for etype in etypes:
            print "Expt type:", etype
            if etype.startswith('opex') or etype == 'xnat:mrSessionData':
                # fields = self.conn.inspect.prefixs(etype)
                # columns = [etype + '/ID',etype + '/SUBJECT_ID',etype + '/DATE',etype + '/INTERVAL',etype + '/DATA_VALID',etype + '/SAMPLE_QUALITY']
                columns = [etype + '/ID', etype + '/SUBJECT_ID', etype + '/DATE']
                criteria = [(etype + '/SUBJECT_ID', 'LIKE', '*'), 'AND']
                df_dates = self.xnat.getSubjectsDataframe(projectcode, etype, columns, criteria)
                if df_dates is not None:
                    aggreg = {'subject_id': {etype: 'count'}, 'date': {etype + '_date': 'min'}}
                    df_counts = df_dates.groupby('subject_id').agg(aggreg).reset_index()
                    # df_counts.columns = df_counts.index.droplevel(level=0)
                    df_counts.columns = ['subject_id', etype + '_visit', etype]
                    df_subjects = df_subjects.merge(df_counts, how='left', on='subject_id')
                    #print len(df_subjects)

        print(df_subjects.head())

        return df_subjects

    def downloadOPEXExpts(self, projectcode, outputdir, deltas=False):
        '''
        CSV downloads for each expt type
        :param projectcode:
        :return:
        '''
        etypes = sorted(self.xnat.conn.inspect.datatypes())
        columns = ['xnat:subjectData/SUBJECT_LABEL', 'xnat:subjectData/SUB_GROUP',
                   'xnat:subjectData/GENDER_TEXT', 'xnat:subjectData/DOB']
        etypes.append('xnat:subjectData')
        try:
            for etype in etypes:
                if etype.startswith('opex'):
                    fields = self.xnat.conn.inspect.datatypes(etype)
                    fields = columns + fields
                    # print(fields)
                    criteria = [(etype + '/SUBJECT_ID', 'LIKE', '*'), 'AND']
                    df_expts = self.xnat.getSubjectsDataframe(projectcode, etype, fields, criteria)
                    if df_expts is not None:
                        msg = "Expt type: %s = %d expts" % (etype,len(df_expts))
                        logging.info(msg)
                        print msg
                        outputname = etype.replace(":", "_") + ".csv"
                        df_expts.to_csv(join(outputdir, outputname), index=False)
                        if deltas:
                            df_delta = self.deltaValues(df_expts)
                            if not df_delta.empty:
                                deltaname = outputname.replace(".csv", "_delta.csv")
                                df_delta.to_csv(join(outputdir, deltaname), index=False)
                                print 'Deltas:', deltaname
                    else:
                        msg = "Expt type: %s - No data", etype
                        logging.warning(msg)
        except Exception as e:
            raise ValueError(e)
        return True

    def deltaValues(self, df_expts):
        """
        Replace data with delta values
        ie interval data - baseline data
        :param df_expts: dataframe with expt data from download
        :param etype: xnat namespace
        :return: dataframe with delta values
        """
        rtn = pandas.DataFrame()
        df_deltas = df_expts.copy()
        df_ints = df_expts.groupby('interval')
        excludes = ['age', 'date', 'insert_date', 'interval', 'project', 'sample_id', 'data_valid', 'comments',
                    'xnat_subjectdata_dob', 'expt_id', 'insert_date', 'insert_user', 'interval', 'project',
                    'sample_id', 'sample_quality', 'status', 'subject_id', 'xnat_subjectdata_dob', 'birth',
                    'xnat_subjectdata_gender_text', 'xnat_subjectdata_sub_group', 'xnat_subjectdata_subject_label']
        if len(df_ints.groups) > 1:
            b = '0'  # baseline
            for k in sorted(df_ints.groups.keys()):
                if k == '0':
                    continue
                for s in df_expts.iloc[df_ints.groups[k].values]['subject_id']:
                    baseline = df_expts.iloc[df_ints.groups[b].values].loc[df_expts['subject_id'] == s]
                    data = df_expts.iloc[df_ints.groups[k].values].loc[df_expts['subject_id'] == s]
                    if len(baseline) != 1 or len(data) != 1:
                        # multiple lines or none - maybe Bloods
                        continue
                    for field in df_expts.columns:
                        #print 'Check field=', field
                        if field in excludes or not field in data or 'comments' in field \
                                or (len(baseline[field].values[0]) <= 0) \
                                or (len(data[field].values[0]) <= 0):
                            msg = "Exclude Field=%s val=%s" % (field, data[field].values[0])
                            logging.debug(msg)
                            continue
                        # %change if not zero baseline
                        bval = float(baseline[field].values[0])
                        if bval != 0:
                            diff = 100 * (float(data[field].values[0]) - bval) / bval
                            msg = "PercentDiff: Field=%s int=%s diff=%s" % (field, k, str(diff))
                            logging.debug(msg)
                        else:
                            diff = float(data[field].values[0]) - bval
                            msg = "Diff: Field=%s int=%s diff=%s" % (field, k, str(diff))
                            logging.debug(msg)
                        df_deltas.at[data.index[0], field] = diff
                        df_deltas.at[baseline.index[0], field] = 0
            else:
                rtn = df_deltas
        return rtn

    def formatCounts(self, df_counts):
        """
        Format counts dataframe with headers in order
        :param df-counts: produced by Xnatconnector.getOPEXExpts
        :return:
        """
        if not df_counts.empty:
            # print(df_counts.columns)
            df_counts['MONTH'] = df_counts['first_visit'].apply(lambda d: self.getMONTH(d))
            # rename columns
            df_counts.rename(columns={'sub_group': 'Group', 'subject_label': 'Subject', 'gender_text': 'M/F'},
                             inplace=True)
            for i in range(len(self.opex)):
                df_counts.rename(columns={self.opex['xsitype'].iloc[i]: self.opex['Expt'].iloc[i]}, inplace=True)
            # reorder columns
            headers = ['MONTH', 'Subject', 'Group', 'M/F'] + list(self.opex['Expt'])
            headers_present = [h for h in headers if h in df_counts.columns]
            df_counts = df_counts[headers_present]
            # save to file as cache if db down
            df_counts.to_csv(self.cache, index=False)
            print df_counts.head()

        return df_counts

    def getMONTH(self, vdate, formatstring='%Y-%m-%d'):
        """
        Calculate MONTH in trial from first visit date
        :param vdate: datetime.datetime object
        :return: interval as 0,1,2 ...
        """
        months = 0
        if isinstance(vdate, str) and len(vdate) > 0:  # and not isinstance(vdate, datetime):
            vdate = datetime.strptime(vdate, formatstring)
        else:
            return months
        tdate = datetime.today()
        dt = tdate - vdate
        if dt.days > 0:
            months = int(dt.days // 30)
        return months

    def maxValue(self, row):
        """
        Function per row - assumes first two are MONTH, Subject
        :param row:
        :return: max of values in row
        """
        val = row[2:].max()
        # print "Val=",val
        # int(max(row.iloc[0, 1:].values)
        return int(val)

    def calculateMissing(self, row):
        """
        Function per row - replace counts with missing
        :param row:
        :return:
        """
        for i, info in self.opex.iterrows():
            # print row
            hdr = info['Expt']
            if hdr in row:
                # if reached max - none missing
                if row[hdr] >= info['total']:
                    row[hdr] = 0
                else:
                    row[hdr] = len(range(self.minmth, row['MONTH'], info['interval'])) - row[hdr]
        return row

    def printMissingExpts(self, projectcode=None):
        """
        Print expt counts with true/false if complete data set for current MONTH
        :param self:
        :return:
        """
        data = self.getExptCounts(projectcode)
        if data is None or data.empty:  # use cached data
            data = self.data
        # Filter groups
        if 'Group' in data.columns:
            data = data[data.Group != 'withdrawn']
        headers = ['MONTH', 'Subject'] + list(self.opex['Expt'])
        headers_present = [h for h in headers if h in data.columns]
        report = data[headers_present]
        if 'MONTH' not in report:
            report['MONTH'] = report.apply(self.maxValue, axis=1)
        report = report.apply(self.calculateMissing, axis=1)
        # Only one CANTAB
        report = report.drop(['CANTAB ERT', 'CANTAB MOT', 'CANTAB PAL', 'CANTAB SWM'], axis=1)
        # print report
        return report

    def getMultivariate(self, expts):
        """
        List of expts from XNAT as collection
        :param expts:
        :return:
        """
        expts = pandas.DataFrame([e for e in expts])
        print expts

        # Group
        # df_grouped = groups.groupby(by='Group')
        # df_grouped.plot.bar(x='Group',y=cols[2:])
        # df_AIT = df_grouped.get_group('AIT')
        # df_MIT = df_grouped.get_group('MIT')
        # df_LIT = df_grouped.get_group('LIT')

    def formatDobNumber(self, orig):
        """
        Reformats DOB string from Excel data float to yyyy-mm-dd
        """
        dateoffset = 693594
        dt = datetime.fromordinal(dateoffset + int(orig))
        return dt.strftime("%Y-%m-%d")

    def groupedCantabOutput(self, df_all, outputfile):
        """
        Output grouped data into Excel
        :param df_all:
        :return:
        """
        writer = pandas.ExcelWriter(outputfile, engine='xlsxwriter')
        df_all.to_excel(writer, index=False, sheet_name='ALL')
        df_grouped = df_all.groupby(by='group')
        for group in ['AIT', 'MIT', 'LIT']:
            df_gp = df_grouped.get_group(group)
            df_gp_intervals = df_gp.groupby(by='interval')
            for interval in sorted(list(df_gp_intervals.groups.keys())):
                sheet = group + '_' + interval
                # print sheet
                df1 = df_gp_intervals.get_group(interval)
                df1.to_excel(writer, index=False, sheet_name=sheet)
        else:
            print "Done"

    # def groupedBloodOutput(self, df_all, outputfile):
    #     """
    #     Output grouped data into Excel
    #     :param df_all:
    #     :return:
    #     """
    #     writer = pandas.ExcelWriter(outputfile, engine='xlsxwriter')
    #     df_all.to_excel(writer, index=False, sheet_name='ALL')
    #     df_grouped = df_all.groupby(by='group')
    #     for group in ['AIT', 'MIT', 'LIT']:
    #         df_gp = df_grouped.get_group(group)
    #         df_gp_intervals = df_gp.groupby(by='interval')
    #         for interval in sorted(list(df_gp_intervals.groups.keys())):
    #             sheet = group + '_' + interval
    #             # print sheet
    #             df1 = df_gp_intervals.get_group(interval)
    #             df1.to_excel(writer, index=False, sheet_name=sheet)
    #     else:
    #         print "Done"

    def generateCantabReport(self, projectcode, outputdir, deltas=None):
        """
        Generates combined CANTAB Report with validated data
        :param outputdir:
        :return: true if OK
        """
        etypes = ['opex:cantabDMS',
                  'opex:cantabERT',
                  'opex:cantabMOT',
                  'opex:cantabPAL',
                  'opex:cantabSWM']
        columns = ['xnat:subjectData/SUBJECT_LABEL',
                   'xnat:subjectData/SUB_GROUP',
                   'xnat:subjectData/GENDER_TEXT']
        outputname = "opex_CANTAB_ALL.xlsx"
        cantabfields = pandas.read_csv(join(self.resource_dir, 'cantab_fields.csv'))
        cantabfields.replace(np.nan, '', inplace=True)
        cantabcolumns = {'xnat_subjectdata_sub_group': 'group',
                         'xnat_subjectdata_subject_label': 'subject',
                         'age': 'age',
                         'xnat_subjectdata_gender_text': 'gender',
                         # 'xnat_subjectdata_dob':'yob','birth':'dob',
                         'data_valid': 'data_valid',
                         'date': 'date', 'interval': 'interval'}

        df_all = pandas.DataFrame()

        try:
            for etype in etypes:
                if etype.startswith('opex'):
                    fields = self.xnat.conn.inspect.datatypes(etype)
                    fields = columns + fields
                    # print(fields)
                    criteria = [(etype + '/SUBJECT_ID', 'LIKE', '*'), 'AND']
                    df_expts = self.xnat.getSubjectsDataframe(projectcode, etype, fields, criteria)
                    # df_expts.set_index('expt_id')
                    if df_expts is not None:
                        df_expts = df_expts[df_expts.data_valid != 'Invalid']
                        msg = "Merging Expt type: %s = %d expts" % (etype, len(df_expts))
                        logging.info(msg)
                        print msg
                        if df_all.empty:
                            df_expts = df_expts.rename(columns=cantabcolumns)
                            df_all = df_expts
                        else:
                            df_all = pandas.merge(df_all, df_expts, how='left',
                                                  left_on=['subject_id', 'interval'],
                                                  right_on=['subject_id', 'interval'], copy=False)
            else:  # save combined output
                allcolumns = cantabcolumns.values()
                for header in cantabfields.columns:
                    cfields = [c.lower() for c in cantabfields[header].values.tolist() if c != '']
                    allcolumns += cfields
                    # print 'cantabfields', cantabfields[header]
                df_all = df_all[allcolumns]
                # output
                outputfile = join(outputdir, outputname)
                self.groupedCantabOutput(df_all, outputfile)
                print "CANTAB Reports: ", outputname
                # deltas
                if deltas:
                    df_deltas = self.deltaValues(df_all)
                    outputfile = outputfile.replace('.xlsx', '_deltas.xlsx')
                    self.groupedCantabOutput(df_deltas, outputfile)
                    print "CANTAB Reports (deltas): ", outputname
                return True
        except Exception as e:
            logging.error(e)
            print e


    def generateBloodReport(self, projectcode, outputdir,deltas):
        """
        Create Blood Report - using pre and post data
        :param outputdir:
        :return:
        """
        etypes = {'COBAS':'opex:bloodCobasData',
                  'ELISAS':'opex:bloodElisasData',
                  'MULTIPLEX':'opex:bloodMultiplexData'}
        columns = ['xnat:subjectData/SUBJECT_LABEL',
                   'xnat:subjectData/SUB_GROUP',
                   'xnat:subjectData/GENDER_TEXT']
        outputfile = join(outputdir,"opex_BLOOD_PREPOST.xlsx")
        datafields = pandas.read_csv(join(self.resource_dir, 'blood_fields.csv'))
        datafields.replace(np.nan, '', inplace=True)

        datacolumns = {'xnat_subjectdata_sub_group': 'group',
                       'xnat_subjectdata_subject_label': 'subject',
                       'age': 'age',
                       'xnat_subjectdata_gender_text': 'gender',
                       'data_valid': 'data_valid',
                       'date': 'date', 'interval': 'interval'}
        d ={'0':'baseline','1':'1m','2':'2m','3':'3m','4':'4m','5':'5m','6':'6m'}
        mths = OrderedDict(sorted(d.items(), key=lambda t: t[0]))
        # setup storage
        cols = ['subject','group'] + [c for c in mths.values()]
        df0 = pandas.DataFrame(columns=cols)
        df0['subject'] = self.subjects['subject_label'].values.tolist()
        df0['group'] = self.subjects['sub_group'].values.tolist()
        all = dict()
        for hdr in datafields.keys():
            for field in datafields[hdr]:
                if len(field) > 0:
                    all[field] = df0.copy()
        #load data from xnat
        try:
            for ex in etypes.keys():
                etype = etypes[ex]
                if etype.startswith('opex'):
                    fields = self.xnat.conn.inspect.datatypes(etype)
                    fields = columns + fields
                    # print(fields)
                    criteria = [(etype + '/SUBJECT_ID', 'LIKE', '*'), 'AND']
                    df_expts = self.xnat.getSubjectsDataframe(projectcode, etype, fields, criteria)
                    if df_expts is not None:
                        df_expts = df_expts.rename(columns=datacolumns)
                        df_expts = df_expts[df_expts.data_valid != 'Invalid']

                        # df_groups = df_expts.groupby('group')
                        # for group in df_groups.groups.keys():
                        #     df_gp = df_groups.get_group(group)
                        df_subjects = df_expts.groupby('subject')
                        for subj in df_subjects.groups.keys():
                            #print subj
                            i = df0[df0['subject'] == subj].index[0]
                            srows = df_subjects.get_group(subj)
                            s_ints = srows.groupby('interval')
                            baseline = s_ints.get_group('0')
                            if len(baseline) < 2:
                                print "insufficient data - ", subj
                                continue

                            for mth in sorted(s_ints.groups.keys()):
                                smth = s_ints.get_group(mth)
                                postval = smth[smth['prepost']=='post']
                                preval = smth[smth['prepost']=='pre']
                                for field in datafields[ex]:
                                    if len(field) > 0:
                                        lfield = field.lower()
                                        if self.validBloodData(preval[lfield]) and self.validBloodData(postval[lfield]):
                                            p0=float(postval[lfield].values[0])
                                            p1=float(preval[lfield].values[0])
                                            all[field].at[i,mths[mth]]=p1-p0 #100 * (p1-p0)/p0
            else:
                print "PrePost Blood Report: Compilation Complete, generating plots ..."
                for field in all.keys():
                    df_all = all[field]
                    df_all.fillna('', axis=1, inplace=True)
                    subdir = join(outputdir, 'BLOOD_PREPOST_RawDiff')
                    if not access(subdir, R_OK):
                        mkdir(subdir)
                    self.plotBloodData(df_all, field, mths, subdir,'Post - Pre')
                    # subdir = join(outputdir, 'BLOOD_PREPOST_Histograms')
                    # if not access(subdir, R_OK):
                    #     mkdir(subdir)
                    # self.plotHistograms(df_all, field, mths, subdir,'Post - Pre')
                if deltas:
                    # generate deltas
                    percent = False
                    all = self.deltaBlood(all, mths,percent)
                    # output to file
                    self.outputBloodData(outputfile, all)
                    # subset deltas data for plots
                    subdir = join(outputdir, 'BLOOD_PREPOST_DeltaBaseline')
                    if not access(subdir, R_OK):
                        mkdir(subdir)
                    deltas = all
                    prefix='delta'
                    # plots per param
                    for field in deltas.keys():
                        df_all = deltas[field]
                        cols = [(prefix + '_' + mth, mth) for mth in mths.values()]
                        rmths = dict(cols)
                        df_all.drop(mths.values(), inplace=True, axis=1)
                        df_all.rename(columns=rmths, inplace=True)
                        df_all.fillna('', axis=1, inplace=True)
                        self.plotBloodData(df_all, field, mths, subdir,'Baseline delta')
                    
                return True

        except Exception as e:
            print e

    # ---------------------------------------------------------------------- #
    def diffValue(self,row,mth, percent):
        """
        Difference of values to baseline as raw diff or percentage of baseline
        :param row: 
        :param mth: 
        :param percent: 
        :return: 
        """
        # filter absent baseline values and missing values
        if row['baseline'] == np.nan or row['baseline'] == '' or row['baseline'] == 0.0 or row[mth] == np.nan or row[mth] == '':
            rtn = np.nan
        else:
            if percent:
                rtn = 100* ((row[mth]-row['baseline'])/row['baseline'])
            else:
                rtn = row[mth] - row['baseline']
        return rtn
        
    def deltaBlood(self,all, mths, percent=False):
        for field in all.keys():
            for mth in mths.values():
                if percent:
                    subfield='percentdelta_'+mth
                else:
                    subfield='delta_' + mth
                all[field][subfield] = all[field].apply(lambda r: self.diffValue(r, mth,percent), axis=1)

        return all


    # ---------------------------------------------------------------------- #
    def outputBloodData(self, outputfile,all):
        writer = pandas.ExcelWriter(outputfile, engine='xlsxwriter')
        for field in all.keys():
            df_all = all[field]
            df_all.to_excel(writer, index=False, sheet_name=field)
            df_grouped = df_all.groupby(by='group')
            for group in ['AIT', 'MIT', 'LIT']:
                df_gp = df_grouped.get_group(group)
                sheet = field + '_' + group
                #print sheet
                df_gp.to_excel(writer, index=False, sheet_name=sheet)

        else:
            return outputfile

    # ---------------------------------------------------------------------- #
    def validBloodData(self,seriesdata):
        rtn = True
        if seriesdata.empty:
            rtn = False
        elif len(seriesdata.values[0])<= 0:
            rtn = False
        return rtn

    # ---------------------------------------------------------------------- #
    def plotBloodData(self, df, title,mths,outputdir, ytitle):
        """
        Plot all fields as subplots vs time
        :param seriesdata:
        :return:
        """
        df.fillna('', inplace=True)
        df_groups = df.groupby(by='group')
        fig = tools.make_subplots(rows=3, cols=1,shared_xaxes=True, subplot_titles=('AIT','MIT','LIT'))
        row = 1
        xlabels = [int(x) for x in mths.keys()]

        for group in ['AIT','MIT','LIT']:
            df1 =df_groups.get_group(group)
            for s in df.subject:
                if not df1[df1['subject'] == s][mths.values()].empty:
                    fig.append_trace(
                        go.Scatter(
                            x=xlabels,
                            y=df1[df1['subject'] == s][mths.values()].values[0],
                            name=s
                        ),row=row,col=1)
            else:
                row +=1
        fig['layout']['title']= title + ": " + ytitle
        fig['layout']['xaxis1']['title']='Interval (month)'
        fig['layout']['yaxis2']['title'] = ytitle
        #Online plot (qbisoftware)
        #py.plot(fig)
        # Create plotly plot
        pfilename = join(outputdir, title +'.html')
        offline.plot(fig, filename=pfilename)
        print "Plot output: ", pfilename
        return pfilename

        # ---------------------------------------------------------------------- #
    def plotHistograms(self, df, title, mths, outputdir, ytitle):
        """
        Plot all fields as subplots vs time
        :param seriesdata:
        :return:
        """
        df.fillna('', inplace=True)
        df_groups = df.groupby(by='group')
        places = []
        maxrows = 4
        maxcols = 2
        for i in range(1, maxrows+1):
            for j in range(1, maxcols+1):
                places.append((i,j))
        colours={'AIT':'red','MIT':'green','LIT':'blue'}
        fig = tools.make_subplots(rows=4, cols=2, shared_xaxes=True, subplot_titles=mths.values())
        ctr = 0
        xlabels = [int(x) for x in mths.keys()]
        for mth in mths.values():

            for group in ['AIT', 'MIT', 'LIT']:
                df1 = df_groups.get_group(group)
                fig.append_trace(
                    go.Histogram(
                        x=df1[mth],
                        cumulative=dict(enabled=True),
                        histnorm='probability',
                        legendgroup=group,
                        name=group,
                        opacity=0.7,
                        marker={'color':colours[group]}
                    ), row=places[ctr][0], col=places[ctr][1])
            else:
                ctr += 1
        fig['layout']['title'] = title + ": " + ytitle
        #fig['layout']['xaxis1']['title'] = ytitle
        #fig['layout']['yaxis2']['title'] = 'Probability'
        fig['layout']['barmode']='overlay'
        # Online plot (qbisoftware)
        # py.plot(fig)
        # Create plotly plot
        pfilename = join(outputdir, title + '.html')
        offline.plot(fig, filename=pfilename)
        print "Plot output: ", pfilename
        return pfilename

########################################################################

if __name__ == "__main__":
    from xnatconnect.XnatConnector import XnatConnector  # Only for testing

    parser = argparse.ArgumentParser(prog='OPEX Report',
                                     description='''\
            Script for reports of QBI OPEX XNAT db
             ''')
    parser.add_argument('database', action='store', help='select database config from xnat.cfg to connect to')
    parser.add_argument('projectcode', action='store', help='select project by code')
    parser.add_argument('--cache', action='store', help='use a downloaded csv file - no connection')
    parser.add_argument('--output', action='store', help='output directory for csv files')

    args = parser.parse_args()
    print "Connecting to database"
    home = expanduser("~")
    configfile = join(home, '.xnat.cfg')
    database = args.database
    projectcode = args.projectcode
    xnat = XnatConnector(configfile, database)
    print "Connecting to URL=", xnat.url
    xnat.connect()
    try:
        print "...Connected"
        subjects = xnat.getSubjectsDataframe(projectcode)
        msg = "Loaded %d subjects from %s : %s" % (len(subjects), database, projectcode)
        print msg
        op = OPEXReport(subjects=subjects)
        op.xnat = xnat
        df = op.getParticipants()
        print df
        # Download CSV files
        if args.output is not None and args.output:
            outputdir = args.output
            #op.downloadOPEXExpts(projectcode=projectcode, outputdir=outputdir, deltas=True)
            #op.generateCantabReport(projectcode=projectcode, outputdir=outputdir, deltas=True)
            op.generateBloodReport(projectcode=projectcode, outputdir=outputdir, deltas=True)

    except ValueError as e:
        print "Error: ", e
    finally:
        xnat.conn.disconnect()
        print("FINISHED")
