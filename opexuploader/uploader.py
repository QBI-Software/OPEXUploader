
"""
    Control module for OPEX upload application
    *******************************************************************************
    Copyright (C) 2017  QBI Software, The University of Queensland

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
"""
__version__ = '1.3.0'
__author__ = 'Liz Cooper-Williams'



import argparse
import csv
import glob
import logging
import sys
import shutil
import pandas as pd
import re
import os
from os import R_OK, access, listdir, mkdir, listdir
from os.path import expanduser, join, basename, exists, dirname, abspath, splitext

from numpy import isnan, nan

from requests.exceptions import ConnectionError
sys.path.append(os.getcwd())
print(sys.path)

from pyxnat.core.errors import DatabaseError
from opexuploader.dataparser.AcerParser import AcerParser
# from opexuploader.dataparser.AmunetParser import AmunetParser, generateAmunetdates
from opexuploader.dataparser.amunetParser_new import amunetParser
from opexuploader.dataparser.BloodParser import BloodParser
from opexuploader.dataparser.CantabParser import CantabParser
from opexuploader.dataparser.CosmedParser import CosmedParser
from opexuploader.dataparser.SFParser import SF36Parser
from opexuploader.dataparser.DexaParser import DexaParser
from opexuploader.dataparser.FitbitParser_new import FitbitParser
from opexuploader.dataparser.BpaqParser import BpaqParser
from opexuploader.dataparser.MridataParser import MridataParser
from opexuploader.dataparser.VisitParser import VisitParser
from opexuploader.dataparser.DassParser import DassParser
from opexuploader.dataparser.GodinParser import GodinParser
from opexuploader.dataparser.PsqiParser import PsqiParser
from opexuploader.dataparser.InsomniaParser import InsomniaParser
from opexuploader.dataparser.IpaqParser import IpaqParser
from opexuploader.dataparser.AccelParser import AccelParser
from opexuploader.dataparser.FoodDiaryParser import FoodDiaryParser
from opexuploader.dataparser.FcasParser import FcasParser
from opexuploader.dataparser.PacesParser import PacesParser
from opexuploader.dataparser.MRIParser import MRIParser
from opexuploader.dataparser.FmriParser import FMRIParser
from opexuploader.dataparser.MissingParser import MissingParser
from opexuploader.dataparser.AdherenceParser import AdherenceParser
from opexuploader.dataparser.MRIParserJunjie import JunjieParser
from opexuploader.dataparser.fMRITaskParser import fMRITaskParser

from xnatconnect.XnatConnector import XnatConnector

from logging.handlers import RotatingFileHandler

### Global config for logging required due to redirection of stdout to console in app
logfile=join(expanduser('~'),'logs','xnatupload.log')
if logfile is not None:
    logbase = dirname(abspath(logfile))
    if not access(logbase, R_OK):
        mkdir(logbase)

logging.basicConfig(filename=logfile,
                    level=logging.INFO,
                    format='%(asctime)s [%(filename)s %(lineno)d] %(message)s',
                    datefmt='%d-%m-%Y %I:%M:%S %p')
logger = logging.getLogger('opex')
handler = RotatingFileHandler(filename=logfile, maxBytes=4000000000)
logger.addHandler(handler)
#
#
class OPEXUploader():
    def __init__(self, args):
        self.args = args
        self.configfile = None
        self.xnat = None

    def config(self):
        # get current user's login details (linux) or local file (windows)
        home = expanduser("~")
        configfile = join(home, '.xnat.cfg')
        if self.args.config is not None:
            configfile = self.args.config
        try:
            access(configfile, R_OK)
            self.configfile = configfile
        except:
            raise ValueError('Config file not found')

    def xnatconnect(self):
        self.xnat = XnatConnector(self.configfile, self.args.database)
        try:
            self.xnat.connect()
        except DatabaseError as e:
            print('Unable to connect to database: Check URL and authentication')

    def xnatdisconnect(self):
        self.xnat.conn.disconnect()

    #------------------------------------------------------------------------------------
    def outputChecks(self, projectcode, matches, missing, inputdir, f2):
        """
        Test run without actual uploading
        :param matches: List of matched participant IDs
        :param missing: Data rows for missing participants
        :param inputdir: Data directory
        :param filename: Report filename
        :return: report filenames of missing and matched files
        """
        reportdir = join(inputdir, "report")
        if not exists(reportdir):
            mkdir(reportdir)
        filename = basename(f2)
        match_filename = join(reportdir, filename + "_matched.csv")
        missing_filename = join(reportdir, filename + "_missing.csv")
        with open(match_filename, 'wb') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            spamwriter.writerow(['Matched ID'])
            for m in sorted(matches):
                spamwriter.writerow([m])

        # Missing subjects
        with open(missing_filename, 'wb') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            spamwriter.writerow(['Missing participants in XNAT'])
            df_sids = self.xnat.getSubjectsDataframe(projectcode)
            for m in missing:
                rid = m['ID'][0:4]
                guess = [sid for sid in df_sids['subject_label'] if rid in sid]
                if len(guess) <= 0:
                    guess = ""
                else:
                    guess = "Possible ID: " + ",".join(guess)
                spamwriter.writerow([m['ID'], guess])
                if not isinstance(m['rows'], dict):
                    for i, row in m['rows'].iterrows():
                        if ('Row Number' in row):
                            spamwriter.writerow(["Row:", row['Row Number']])
                        else:
                            spamwriter.writerow(["Row:", i])

        if self.args.checks is not None and self.args.checks:
            msg = "*******TEST RUN ONLY*******\n"
        else:
            msg = "*******XNAT UPLOADED*******\n"

        msg = "%sMatched participants: %d\nMissing participants: %d\n" % (msg, len(matches), len(missing))
        logging.info(msg)
        print(msg)

        return (match_filename, missing_filename)

    # ------------------------------------------------------------------------------------
    def loadSampledata(self, subject, samplexsd, sampleid, mandata, sampledata):
        """ Loads sample data from CANTAB data dump
        Check if already exists - don't overwrite (allows for cumulative data files to be uploaded)
        :param sampleid: ID for this row of CANTAB data
        :param i: row number of dataset
        :param row: row as pandas series with data
        :param subject: subject to add experiment to
        :return: msg for logging
        """
        expt = subject.experiment(sampleid)

        if (self.args.update is not None):
            update = self.args.update
        else:
            update = False

        if not expt.exists() or update:
            self.xnat.createExperiment(subject, samplexsd, sampleid, mandata, sampledata)
            msg = 'Experiment created:' + sampleid
        else:
            msg = 'Experiment already exists: ' + sampleid


        return msg

    # ------------------------------------------------------------------------------------

    def experiment_exists(self, subject, sampleid):

        expt = subject.experiment(sampleid)

        if not expt.exists():
            msg = str(subject) + ":" + str(sampleid) + " does not exist-----------------------------"

        else:
            msg = str(subject) + ":" + str(sampleid) + " EXISTS!!!!!!!!!!!!!!!!!!"

        return msg

    def loadAMUNETdata(self, sampleid, i, row, subject, amparser):
        """ Loads AMUNET sample data from data dump
        Data is combined from two source files
        Check if expt already exists - don't overwrite (allows for cumulative data files to be uploaded)
        :param sampleid: ID for this row of data
        :param i: row number of dataset
        :param row: row as pandas series with data
        :param subject: subject to add experiment to
        :return: msg for logging
        """
        motid = sampleid
        motxsd = amparser.getxsd()
        expt = subject.experiment(motid)

        if not expt.exists() or (self.args.update is not None and self.args.update):
            # two files with different columns merged to one
            if 'AEV_Average total error' in row:
                (mandata, motdata) = amparser.mapAEVdata(row, i)
            else:
                (mandata, motdata) = amparser.mapSCSdata(row, i)
            # motdata[motxsd + '/date'] = amparser.dates[motid]
            self.xnat.createExperiment(subject, motxsd, motid, mandata, motdata)
            msg = 'Amunet experiment created:' + motid

        elif (len(expt.xpath('opex:AEV')) > 0 and len(
                expt.xpath('opex:SCS')) == 0 and 'SCS_Average total error' in row):  # loaded AEV data but not SCS
            e1 = expt
            (mandata, motdata) = amparser.mapSCSdata(row, i)
            e1.attrs.mset(motdata)
            msg = 'Amunet experiment updated with SCS: ' + motid

        elif (len(expt.xpath('opex:SCS')) > 0 and len(
                expt.xpath('opex:AEV')) == 0 and 'AEV_Average total error' in row):  # loaded SCS data but not AEV
            e1 = expt
            (mandata, motdata) = amparser.mapAEVdata(row, i)
            e1.attrs.mset(motdata)
            msg = 'Amunet experiment updated with AEV: ' + motid
        else:
            msg = 'Amunet experiment already exists: ' + motid
        return msg

    # ------------------------------------------------------------------------------------
    def uploadData(self, project, dp):
        """
        Upload data via specific Data parser
        :param dp:
        :return: missing and matches
        """
        missing = []
        matches = []
        if dp.subjects is None or len(dp.subjects) <= 0:
            print("Uploader - sorting subjects")
            dp.sortSubjects()
        #get list of subjects - single call
        #df_xnatsubjects = self.xnat.getSubjectsDataframe(project)
        for sd in dp.subjects:
            print('*****SubjectID:', sd)
            sd = str(sd) #prevent unicode
            s = project.subject(sd)
            if not s.exists():

                if self.args.create is not None and self.args.create:
                    # create subject in database
                    skwargs = dp.getSubjectData(sd)
                    s = self.xnat.createSubject(project.id(), sd, skwargs)
                    msg = 'Subject CREATED: %s' % sd
                    logging.info(msg)
                    print(msg)
                else:
                    missing.append({"ID": sd, "rows": dp.subjects[sd]})
                    msg = 'Subject does not exist - skipping: %s' % sd
                    logging.warning(msg)
                    print(msg)
                    continue
            # Load data PER ROW
            matches.append(sd)
            if self.args.checks is None or not self.args.checks:  # Don't upload if checks

                try:
                    xsd = dp.getxsd()
                    if isinstance(xsd,dict) and 'opex:cantabMOT' in list(xsd.values()): #cantab
                        #print('Running cantab upload')
                        xsdtypes = xsd
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd, row)
                            row.replace(nan, '', inplace=True)
                            if ('NOT_RUN' in row.values) or ('ABORTED' in row.values):
                                msg = "Skipping due to ABORT or NOT RUN: %s" % sampleid
                                logging.warning(msg)
                                print(msg)
                                continue
                            for type in list(xsdtypes.keys()):
                                if str(row[dp.getStatusstring()[type]]) == 'SYSTEM_ERROR':
                                    continue
                                (mandata, data) = dp.mapData(row, i, type)
                                xsd = xsdtypes[type]
                                msg = self.loadSampledata(s, xsd, type + "_" + sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)


                    elif 'food' in xsd:
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd, row)
                            (mandata, data) = dp.mapData(row, i)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                    elif 'fcas' in xsd:
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd, row)
                            (mandata, data) = dp.mapData(row, i)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                    # elif 'dexa' in xsd:
                    #     checkfield = dp.fields['Field'][0]  # test if data in row
                    #     for i, row in dp.subjects[sd].items():
                    #         if checkfield in row and not isnan(row[checkfield].iloc[0]):
                    #             print('Interval:', dp.intervals[i])
                    #             sampleid = dp.getSampleid(sd, i)
                    #             (mandata, data) = dp.mapData(row, i, xsd)
                    #             msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                    #             logging.info(msg)
                    #             if 'created' in msg:
                    #                 print(msg)

                    elif 'fitbit' in xsd:
                        for i, row in dp.subjects[sd].iterrows():
                            interval = int(row['interval'])
                            sampleid = dp.getSampleid(sd, interval)
                            print('Sampleid:', sampleid)
                            (mandata, data) = dp.mapData(row, i)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                    elif 'accelday' in xsd or 'accelmonth' in xsd:
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd, row)
                            (mandata, data) = dp.mapData(i, row)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                    elif 'dexa' in xsd:
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd, row)
                            row.replace(nan, '', inplace=True)
                            (mandata, data) = dp.mapData(row, i, xsd)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                    elif 'dass' in xsd:
                        #print('Loading dass or godin')
                        maxmth = 12
                        intervals = list(range(0, maxmth+1, 3))
                        for i in intervals:
                            iheaders = [c + "_" + str(i) for c in dp.fields]
                            sampleid = dp.getSampleid(sd, i)
                            row = dp.subjects[sd]
                            # row.replace(nan, '', inplace=True)
                            if iheaders[0] in row.columns:
                                if dp.validData(row[iheaders].values.tolist()[0]):
                                    (mandata, data) = dp.mapData(row[iheaders], i, xsd)
                                    msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                    logging.info(msg)
                                    if 'created' in msg:
                                        print(msg)
                                else:
                                    print('empty data - skipping')
                                    continue

                    elif 'godin' in xsd:
                        row = dp.subjects[sd]
                        i = str(int(row['TimePoint']))
                        sampleid = dp.getSampleid(sd, i)
                        # print(sampleid)
                        iheaders = dp.fields
                        if iheaders[0] in row.columns:
                            print('Sampleid:', sampleid)
                            if dp.validData(row[iheaders].values.tolist()[0]):
                                (mandata, data) = dp.mapData(row[iheaders], i, xsd)
                                msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                            else:
                                print('empty data - skipping')
                                continue

                    elif 'paces' in xsd or 'bpaq' in xsd:
                        row = dp.subjects[sd]
                        i = str(int(row['TimePoint']))
                        sampleid = dp.getSampleid(sd, i)
                        # print(sampleid)
                        iheaders = dp.fields
                        if iheaders[0] in row.columns:
                            print('Sampleid:', sampleid)
                            if dp.validData(row[iheaders].values.tolist()[0]):
                                (mandata, data) = dp.mapData(row[iheaders], i)
                                msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                            else:
                                print('empty data - skipping')
                                continue


                    elif 'ipaq' in xsd:
                        interval = 0
                        sampleid = dp.getSampleid(sd, interval)
                        row = dp.subjects[sd]
                        if dp.validData(row.values.tolist()[0]):
                            print(sampleid)
                            (mandata, data) = dp.mapData(row, interval, xsd)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)


                    elif 'acer' in xsd:
                        # print('Loading dass or godin')
                        intervals = [0,6]
                        iheaders = dp.fields
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd,row)
                            if dp.validData(row[iheaders].values.tolist()):
                                (mandata, data) = dp.mapData(row, i, xsd)
                                msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)

                    elif 'sf' in xsd:
                        iheaders = dp.fields
                        for i, row in dp.subjects[sd].iterrows():
                            j = row['interval']
                            sampleid = dp.getSampleid(sd, row)
                            print('Sampleid:', sampleid)
                            if dp.validData(row[iheaders].values.tolist()):
                                (mandata, data) = dp.mapData(row, i, xsd)
                                msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                            else:
                                print('empty data - skipping')
                                continue


                    # elif 'acer' in xsd:
                    #     for i, row in dp.subjects[sd].iterrows():
                    #         sampleid =dp.getSampleid(sd,row)
                    #         print('Sampleid:', sampleid)
                    #         (mandata, data) = dp.mapData(row, i, xsd)
                    #         msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                    #         logging.info(msg)
                    #         if 'created' in msg:
                    #             print(msg)


                    elif 'insomnia' in xsd or 'psqi' in xsd:
                        i = dp.interval
                        sampleid = dp.getSampleid(sd, i)
                        print('Sampleid:', sampleid)
                        row = dp.subjects[sd]
                        # row.replace('nan', '', inplace=True)
                        if dp.validData(row[dp.fields].values.tolist()[0]):
                            (mandata, data) = dp.mapData(row, i, xsd)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)
                        else:
                            print('empty data - skipping')
                            continue


                    elif 'adherence' in xsd:
                        sampleid = dp.getSampleid(sd)
                        print('Sample ID: ' + sampleid)
                        row = dp.subjects[sd]

                        (mandata, data) = dp.mapData(row)
                        msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                        logging.info(msg)
                        if 'created' in msg:
                            print(msg)

                    elif 'cosmed' in xsd:
                        for i, row in list(dp.subjects[sd].items()):
                            sampleid = dp.getSampleid(sd, i)
                            if sampleid in ['COS_1021LB_0', 'COS_1021LB_3']:
                                continue
                            (mandata, data) = dp.mapData(row, i, xsd)

                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                    elif 'missing' in xsd:
                        row = dp.subjects[sd]
                        i = row['interval'].iloc[0]
                        sampleid = dp.getSampleid(sd, i)
                        print('Sampleid:', sampleid)
                        (mandata, data) = dp.mapData(row, i)
                        msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                        logging.info(msg)
                        if 'created' in msg:
                            print(msg)


                    elif 'amunetall' in xsd:
                        print('Running amunet upload')
                        sampleid = dp.getSampleid(sd)
                        (mandata, data) = dp.mapData()
                        print(mandata, data)
                        msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                        logging.info(msg)
                        print(msg)
                        if 'created' in msg:
                            print(msg)

                    elif ('mrifs' in xsd or 'blood' in xsd):
                        for i, row in dp.subjects[sd].iterrows():

                            prefix = dp.getPrefix() if dp.getPrefix() is not None else 'BDNF'

                            if(dp.type == 'SOMATO'):
                                prefix = 'SOMATO'

                            sampleid = prefix + "_" + dp.getSampleid(sd, row)
                            row.replace(nan, '', inplace=True)
                            (mandata, data) = dp.mapData(row, i, xsd)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)

                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)


                    elif ('ashsraw' in xsd or 'ashslong2' in xsd or 'ashslong3' in xsd):
                        sampleid = dp.getSampleid(sd)
                        print('SampleID: ' + sampleid)
                        row = dp.subjects[sd]
                        (mandata, data) = dp.mapData(row)
                        msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                        logging.info(msg)
                        if 'created' in msg:
                            print(msg)

                    elif 'mrijunjie' in xsd:
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd, row)
                            (mandata, data) = dp.mapData(row, i)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                    elif('taskret' in xsd) or ('taskencode' in xsd):
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd, row)
                            (mandata, data) = dp.mapData(row, i)
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                    elif 'fmri' in xsd:
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd, row)
                            print('SampleID: ' + sampleid)
                            (mandata, data) = dp.mapData(row, i)

                            try:
                                msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                logging.info(msg)
                                print(msg)
                                if 'created' in msg:
                                    print(msg)

                            except:
                                pass


                except Exception as e:
                    logging.error(e.args[0])
                    raise ValueError(e)
        return (missing, matches)

    def runDataUpload(self, projectcode, inputdir, datatype):
        """
        Data upload template
        :param projectcode:
        :param inputdir:
        :param kwargs:
        :return: success or error
        """
        print(datatype)
        msg = "Running data upload for %s from %s " % (datatype, inputdir)
        logging.info(msg)
        print(msg)
        project = self.xnat.get_project(projectcode)
        missing = []
        matches = []
        if access(inputdir, R_OK):
            if datatype == 'cantab':
                seriespattern = '*.csv'
                sheet = 0
                skip = 0
                header = None
                etype = 'CANTAB'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    if ("RowBySession" in f2):
                        msg = "\nLoading: %s" % f2
                        print(msg)
                        logging.info(msg)
                        dp = CantabParser(f2, sheet, skip, header, etype)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)

            # ---------------------------------------------------------------------#
            elif datatype == 'adherence':

                files = ['Training-Diary-AIT_20181123.xlsx', 'Training-Diary-MIT_20181123.xlsx',
                         'Training-Diary-LIT_20181220.xlsx']

                for f2 in files:
                    try:
                        path = join(inputdir, f2)
                        print("Loading ", f2)
                        dp = AdherenceParser(filepath=path)
                        (missing, matches) = self.uploadData(project, dp)
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2 + "_")
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)
                    except Exception as e:
                        print("Cannot process file: %s" % e)
                        continue

            # ---------------------------------------------------------------------#
            elif datatype == 'mrijunjie':
                dp = JunjieParser(inputdir=inputdir)
                (missing, matches) = self.uploadData(project, dp)
                # Output matches and missing
                if len(matches) > 0 or len(missing) > 0:
                    (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir)
                    msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                    print(msg)
                    logging.info(msg)
            # ---------------------------------------------------------------------#
            elif(datatype == 'taskret') or (datatype == 'taskencode'):
                dp = fMRITaskParser(inputdir=inputdir)
                (missing, matches) = self.uploadData(project, dp)
                print(missing)
                # Output matches and missing
                if len(matches) > 0 or len(missing) > 0:
                    (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir)
                    msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                    print(msg)
                    logging.info(msg)

            # ---------------------------------------------------------------------#
            elif datatype == 'mrinew':

                # print("Loading " + inputdir)
                # dp = MriParser(inputdir)
                # (missing, matches) = self.uploadData(project, dp)

                rootdir = inputdir
                subdirs = listdir(rootdir)
                etype = basename(rootdir)

                for inputdir in subdirs:
                    if inputdir not in ['0m', '6m', '12m']:
                        continue
                    interval = inputdir[0:-1]
                    print('Interval:', interval)
                    inputdir = join(rootdir, inputdir)
                    dp = MRIParser(inputdir)
                    (missing, matches) = self.uploadData(project, dp)

            # ---------------------------------------------------------------------#
            elif datatype == 'fmri':

                dp = FMRIParser(inputdir=inputdir)
                (missing, matches) = self.uploadData(project, dp)
                # Output matches and missing
                if len(matches) > 0 or len(missing) > 0:
                    (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                    msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                    print(msg)
                    logging.info(msg)


            # ---------------------------------------------------------------------#
            elif datatype == 'amunetall':
                root_dir = inputdir
                # interval_dir = ['1. 0M_Baseline', '2. 3M_Interim', '3. 6M_Post', '4. 9M_Maintenance', '5. 12M_Final']
                interval_dir = ['1. 0M_Baseline']
                errors_path = "Q:\\DATA\\DATA ENTRY\\hMWM results\\errors_template.csv"
                sheet=0

                for i in interval_dir:
                    path = join(root_dir, i)
                    files = [f for f in listdir(path) if splitext(f)[-1] == '.zip' or splitext(f)[-1] == '.xml']
                    for f2 in files:
                        msg = "------------------------- STARTING: " + f2 + " -----------------------------"
                        logging.info(msg)
                        print(msg)
                        filetopath = join(path, f2)
                        try:
                            dp = amunetParser(filetopath)
                            (missing, matches) = self.uploadData(project, dp)
                            # Output matches and missing
                            if len(matches) > 0 or len(missing) > 0:
                                (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2 + "_" + str(sheet))
                                msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                                print(msg)
                                logging.info(msg)
                        except Exception as e:
                            print("Cannot process file: %s" % e)
                            continue
            # ---------------------------------------------------------------------#
            elif datatype == 'sf':
                sheet = 0
                skip = 0
                etype = 'SF36'
                header = 0
                # inputfile = "SF-36 Data 17_09_18_SCORED_RS.xls"
                seriespattern = '*.xls'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("Loading " + f2)
                    dp = SF36Parser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'food':
                sheet = 0
                skip = 1
                header = None
                seriespattern = '*.xlsx'
                etype = 'FOODDIARY'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("Loading ", f2)
                    dp = FoodDiaryParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)



            # ---------------------------------------------------------------------#
            elif datatype == 'fcas':
                skip = 0
                files = [f for f in listdir(inputdir) if splitext(f)[1] == '.xlsx']
                sheet = 0

                for f2 in files:
                    try:
                        dp = FcasParser(inputdir=inputdir, filename=f2)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2 + "_" + str(sheet))
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)
                    except Exception as e:
                        print("Cannot process file: %s" % e)
                        continue

            # ---------------------------------------------------------------------#
            elif datatype == 'acer':
                sheet = 0
                skip = 0
                header = None
                seriespattern = '*.xlsx'
                etype = 'ACER'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("Loading ", f2)
                    for sheet in range(0, 2):
                        print("Interval:")
                        dp = AcerParser(f2, sheet, skip, header, etype)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)

            # ---------------------------------------------------------------------#
            elif datatype == 'mridata':
                seriespattern = '*.xlsx' # the new file is xlsx
                sheet = 0
                skip = 0
                header = None
                etype = 'MRI '
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("Loading ", f2)
                    if 'ASHS' in f2:
                        etype += 'ASHS'
                    elif 'FreeSurf' in f2:
                        etype += 'FS'
                    else:
                        raise ValueError("Cannot determine MRI type")
                    dp = MridataParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir,
                                                         f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'blood':
                seriespattern = '*.xlsx'
                sheet = 0
                skip = 0

                if basename(inputdir) == 'CROSSOVER':
                    type = basename(dirname(inputdir))
                else:
                    type = basename(inputdir)  # assume dir is type eg COBAS to match

                if type == 'MULTIPLEX' or type == 'BDNF':
                    skip = 0
                elif type == 'ELISAS' or type == 'SOMATO':
                    skip = 0
                    sheet = 2
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                if type == 'COBAS':
                    skip = 1
                for f2 in files:
                    print("Loading ", f2)
                    dp = BloodParser(f2, sheet, skip, type=type)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)

            # ---------------------------------------------------------------------#
            elif datatype == 'dexa':
                sheet = 0
                skip = 0
                header = None
                etype = 'DEXA'
                seriespattern = '*.csv'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("Loading ", f2)
                    dp = DexaParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'fitbit':
                sheet = 0
                skip = 0
                header = None
                etype = 'FITBIT'
                seriespattern = '*.csv'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("Loading ")
                    dp = FitbitParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'dass':
                sheet = 0
                skip = 1
                header = None
                etype='DASS'
                seriespattern = '*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("Loading ", f2)
                    dp = DassParser(f2, sheet, skip, header,etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'ipaq':
                sheet = 0
                skip = 2
                header = None
                etype = 'IPAQ'
                seriespattern = '*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                for f2 in files:
                    print("Loading ", f2)
                    dp = IpaqParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'accel':
                sheet = 0
                skip = 0
                header = None
                etype = 'ACC'
                seriespattern = '*.csv'
                files = glob.glob(join(inputdir, seriespattern))
                for f2 in files:
                    print("Loading ", f2)
                    dp = AccelParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'bpaq':
                sheet = 0
                skip = 0
                header = 0
                etype = 'BPAQ'
                seriespattern = '*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))

                for f2 in files:
                    print("Loading ", f2)
                    dp = BpaqParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'godin':
                sheet = 0
                skip = 0
                header = 0
                etype = 'Godin'
                seriespattern = 'GODIN*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                maxmth = 12
                intervals = list(range(0, maxmth + 1, 3))
                for f2 in files:
                    print("Loading ", f2)
                    dp = GodinParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)


                    for sheet in range(0, len(intervals)):
                        i = intervals[sheet]
                        print('Interval:', i)
                        try:
                            dp = GodinParser(f2, sheet, skip, header, etype)
                        except ValueError as e:
                            logging.warning(e)
                            continue
                        dp.interval = i
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)

            # ---------------------------------------------------------------------#
            elif datatype == 'paces':

                skip = 0
                header = 0
                etype = 'PACES'
                seriespattern = 'PACES*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                for f2 in files:
                    print("Loading ", f2)
                    xl = pd.ExcelFile(f2)
                    intervals = [int(re.findall('\\d{1,2}', s)[0]) for s in xl.sheet_names]
                    for sheet in range(0, len(xl.sheet_names)):
                        i = intervals[sheet]
                        print('Interval:', i)
                        dp = PacesParser(f2, sheet, skip, header, etype)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'missing':
                seriespattern = '*.xlsx'
                etype = 'MISS'
                files = glob.glob(join(inputdir, seriespattern))

                for f2 in files:
                    print("Loading ", f2)
                    try:
                        dp = MissingParser(datafile=f2)
                    except ValueError as e:
                        logging.warning(e)
                        continue
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)


            # ---------------------------------------------------------------------#
            elif datatype == 'psqi':
                skip = 1
                header = 1
                etype = 'PSQI'
                seriespattern = 'PSQI*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                maxmth = 12
                intervals = list(range(0, maxmth+1, 3))
                for f2 in files:
                    print("Loading ", f2)
                    for sheet in range(0, len(intervals)):
                        i = intervals[sheet]
                        print('Interval:', i)
                        try:
                            dp = PsqiParser(f2, sheet, skip, header, etype)
                        except ValueError as e:
                            logging.warning(e)
                            continue
                        dp.interval = i
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'insomnia':
                skip = 0
                header = None
                etype = 'Insomnia'
                seriespattern = 'ISI*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                maxmth = 12
                intervals = list(range(0, maxmth + 1, 3))
                for f2 in files:
                    print("Loading ", f2)
                    for sheet in range(0, len(intervals)):
                        i = intervals[sheet]
                        print('Interval:', i)
                        try:
                            dp = InsomniaParser(f2, sheet, skip, header, etype)
                        except ValueError as e:
                            logging.warning(e)
                            continue
                        dp.interval = i
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'cosmed':
                try:
                    if sys.platform == 'win32':
                        pathsfile =join(inputdir, 'xnatpaths1.txt')
                    else:
                        pathsfile = join(inputdir, 'xnatpaths_mac.txt')

                    f = open(pathsfile)
                    paths = {}
                    for p in f.readlines():
                        p = p.rstrip()
                        (k, v) = p.split('=')
                        paths[k] = v
                    inputsubdir = join(paths['datadir'], paths['subdata'])
                    datafile = join(paths['datadir'], paths['datafile'])  # 'VO2data_VEVCO2_20171009.xlsx'
                    msg = 'COSMED: Datafile= %s \nTime series for files in %s ' % (datafile, inputsubdir)
                    logging.info(msg)
                    print(msg)

                    dp = CosmedParser(inputdir, inputsubdir, datafile, self.args.checks)
                    if dp.df.empty:
                        raise ValueError('Data error during compilation - not uploaded to XNAT')
                    else:
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode,
                                                             matches,
                                                             missing,
                                                             inputdir,
                                                             datafile)
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)
                except Exception as e:
                    msg = 'COSMED data access failed - %s' % e.args[0]
                    raise ValueError(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'visit':
                inputfile = join(inputdir, 'Visits.xlsx')
                try:
                    dp = VisitParser(inputfile, 0, 1)
                    dp.processData()

                    if self.args.checks:
                        print("**UPDATING dates [TEST]**")
                        matches =list(dp.expts.keys())
                        for eid in list(dp.expts.keys()):
                            print(eid, dp.expts.get(eid))
                    else:
                        (missing, matches) = dp.uploadDates(projectcode, self.xnat)
                except Exception as e:
                    raise ValueError(e)
            # ---------------------------------------------------------------------#
            elif datatype == 'mri':
                if hasattr(self.args,'opexid'):
                    opexid = self.args.opexid
                else:
                    opexid = False
                if hasattr(self.args,'subjectchars'):
                    snum = self.args.subjectchars
                else:
                    snum = 6
                fid = self.xnat.upload_MRIscans(projectcode, inputdir,opexid, snum)
                if fid == 0:
                    msg = 'Upload not successful - 0 sessions uploaded'
                    print(msg)
                    logging.warning(msg)
                else:
                    msg = "Subject sessions uploaded: %d" % fid
                    print(msg)
                    logging.info(msg)
            # ---------------------------------------------------------------------#
            else:
                msg = "Option not handled: %s" % datatype
                logging.error(msg)
                raise ValueError(msg)
            # ---------------------------------------------------------------------#
            return (missing, matches)


        else:
            msg = "Input directory error: %s" % inputdir
            logging.error(msg)
            raise IOError(msg)


def create_parser():
    parser = argparse.ArgumentParser(prog='OPEX Uploader',
                                     description='''\
            Script for uploading scans and sample data to QBI OPEX XNAT db
             ''')
    parser.add_argument('database', action='store', help='select database config from xnat.cfg to connect to')
    parser.add_argument('projectcode', action='store', help='select project by code')
    # optional
    parser.add_argument('--projects', action='store_true', help='list projects')
    parser.add_argument('--subjects', action='store_true', help='list subjects')
    parser.add_argument('--config', action='store', help='database configuration file (overrides ~/.xnat.cfg)')
    parser.add_argument('--expt', action='store', help='Type of experiment data (must match)')
    parser.add_argument('--exptdata', action='store', help='directory location of experiment data')
    parser.add_argument('--checks', action='store_true', help='Test run with output to files')
    parser.add_argument('--update', action='store_true', help='Also update existing data')
    parser.add_argument('--create', action='store_true', help='Create Subject from input data if not exists')
    return parser


########################################################################
if __name__ == "__main__":
    """
    Example: python uploader.py opex P1 --expt cantab --exptdata "Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\cantab" --checks
    """
    parser = create_parser()
    args = parser.parse_args()
    uploader = OPEXUploader(args)
    uploader.config()
    uploader.xnatconnect()
    logging.info('Connecting to Server:%s Project:%s', uploader.args.database, uploader.args.projectcode)

    try:
        if uploader.xnat.testconnection():
            print("Connected")
            # Check project code is correct
            projectcode = uploader.args.projectcode
            p = uploader.xnat.get_project(projectcode)
            # Test run
            missing = []
            matches = []
            if (not p.exists()):
                msg = "This project [%s] does not exist in this database [%s]" % (projectcode, uploader.args.database)
                raise ConnectionError(msg)
            # List available subjects in project
            if (uploader.args.subjects is not None and uploader.args.subjects):
                msg = "Calling List Subjects"
                print(msg)
                uploader.xnat.list_subjects_all(projectcode)
            # List available projects
            if (uploader.args.projects is not None and uploader.args.projects):
                print("Calling List Projects")
                projlist = uploader.xnat.list_projects()
                for p in projlist:
                    print("Project: ", p.id())

            ################ Upload expt data ################
            # runDataUpload(self, projectcode, inputdir, datatype)
            runoption = args.expt
            rundir = args.exptdata
            uploader.runDataUpload(projectcode, rundir, runoption)

        else:
            raise ConnectionError("Connection failed - check config")
    except IOError as e:
        print("Failed IO:", e)
    except ConnectionError as e:
        print("Failed connection:", e)
    except ValueError as e:
        print("ValueError:", e)
    except Exception as e:
        print("ERROR:", e)
    finally:  # Processing complete
        uploader.xnatdisconnect()
        print("\n****FINISHED**** - see xnatupload.log for details")

