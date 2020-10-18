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
__version__ = '2.2.0'
__author__ = 'Liz Cooper-Williams'

import argparse
import csv
import glob
import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from os import R_OK, access, mkdir, listdir
from os.path import expanduser, join, basename, exists, dirname, abspath, splitext

import pandas as pd
from numpy import nan
from pyxnat.core.errors import DatabaseError
from pyxnat.core.resources import Project
from requests.exceptions import ConnectionError

from opexuploader.dataparser.AccelParser import AccelParser
from opexuploader.dataparser.AmunetParser import AmunetParser, generateAmunetdates
from opexuploader.dataparser.AcerParser import AcerParser
from opexuploader.dataparser.AdherenceParser import AdherenceParser
from opexuploader.dataparser.AmunetParser_XML import AmunetParserXML
from opexuploader.dataparser.BloodParser import BloodParser
from opexuploader.dataparser.BpaqParser import BpaqParser
from opexuploader.dataparser.CantabParser import CantabParser
from opexuploader.dataparser.CosmedParser import CosmedParser
from opexuploader.dataparser.DassParser import DassParser
from opexuploader.dataparser.DexaParser import DexaParser
from opexuploader.dataparser.FcasParser import FcasParser
from opexuploader.dataparser.FitbitParser_new import FitbitParser
from opexuploader.dataparser.FoodDiaryParser import FoodDiaryParser
from opexuploader.dataparser.GodinParser import GodinParser
from opexuploader.dataparser.InsomniaParser import InsomniaParser
from opexuploader.dataparser.IpaqParser import IpaqParser
from opexuploader.dataparser.MissingParser import MissingParser
from opexuploader.dataparser.MridataParser import MridataParser
from opexuploader.dataparser.PacesParser import PacesParser
from opexuploader.dataparser.PsqiParser import PsqiParser
from opexuploader.dataparser.SFParser import SF36Parser
from opexuploader.dataparser.VisitParser import VisitParser
from opexuploader.utils import findResourceDir
from xnatconnect.XnatConnector import XnatConnector

### Global config for logging required due to redirection of stdout to console in app
logfile = join(expanduser('~'), 'logs', 'xnatupload.log')
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

DEBUG = 0  # Flag when Testing

def getMaxMth(type):
    """ For dass, godin, psqi, insomnia - get max month from maxmth.csv """
    rtn = 12
    try:
        resdir = findResourceDir()
        if resdir is not None:
            maxmths = pd.read_csv(join(resdir, 'maxmth.csv'))
            maxmth = maxmths[maxmths['TYPE'] == type]['MAXMTH']
            if maxmth is not None:
                rtn = int(maxmth)
    except ValueError as e:
        print(e)
    return rtn

def detectTabs(dp, intervals):
    """
    Check that correct number of tabs exist
    Used in dass, godin, psqi, insomnia
    :param dp: loaded DataParser
    :param intervals: array of intervals to match tabs
    :return:
    """
    if isinstance(dp, pd.DataFrame):
        fp = dp.datafile
    else:
        fp = dp
    xl = pd.ExcelFile(fp)
    tabs = len(xl.sheet_names)
    return intervals[0:tabs]

### Main class for upload of all dataparser types
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

    # ------------------------------------------------------------------------------------
    def outputChecks(self, projectcode, matches, missing, inputdir, f2):
        """
        Compares Subject IDs in data entry and XNAT database
        Produces a report of any missing Subject IDs - makes a guess if there is a similar number
        *** BUT DOES NOT IMPLEMENT OVERRIDING SUBJECT IDS as this would impair the data integrity ****
        After an upload run, check the report for missing IDs and manually map any incorrect IDs
        to the opexconfig.db -> opexids (this can be done via the GUI)
        - this will be checked during subsequent data loads
        :param projectcode: XNAT project ID
        :param matches: list of matched participant IDs
        :param missing: Data rows for missing participants
        :param inputdir: directory containing data files - will add a subdirectory 'report'
        :param f2: data filename - will add a suffix for matched and missing files
        :return:
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
        msg = "Reports created: \n\t%s\n\t%s" % (match_filename, missing_filename)
        logging.info(msg)
        return (match_filename, missing_filename)

    # ------------------------------------------------------------------------------------
    def loadSampledata(self, subject, samplexsd, sampleid, mandata, sampledata):
        """
        Loads sample data to XNAT from extracted data for input
        Check if experiment already exists - don't overwrite (allows for cumulative data files to be uploaded)
        :param subject: Subject ID
        :param samplexsd: Name of XSD file (opexconfig.db -> expts table -> xsitype)
        :param sampleid: generated unique id for this sample
        :param mandata: mandatory fields
        :param sampledata: fields for this data type (opexconfig.db -> opexfields)
        :return: msg status
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
    def loadAMUNETdata(self, sampleid, i, row, subject, amparser):
        """
        Loads AMUNET sample data to XNAT
        Data is combined from two source files
        Check if expt already exists - don't overwrite (allows for cumulative data files to be uploaded)
        :param sampleid: ID for this row of data
        :param i: row number of dataset
        :param row: row as pandas series with data
        :param subject: subject ID to add experiment to
        :param amparser: Amunet Data parser
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
        ***Upload data via specific Data parser***
        ---------------------------------------------
        1. Get list of subjects loaded in DataParser
        2. If subject is missing in XNAT, will create it (only if create flag is ON)
        3. For each data type,
            generate a sample id according to data type,
            map the data to type fields
            then upload to XNAT
        ie
            sampleid = dp.getSampleid(sd, row)
            (mandata, data) = dp.mapData(row, i)
            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)

        Some types require further information to be included (eg intervals) - this is dependent on the input data files

        :param project: XNAT project object for checking subjects (from xnatconnect)
        :param dp: Data Parser of specific data type (instantiated)
        :return: missing and matched lists of subject IDs
        """
        missing = []
        matches = []
        if dp.subjects is None or len(dp.subjects) <= 0:
            print("Uploader - sorting subjects")
            dp.sortSubjects()
        # For each subject - create SUBJECT if not exists (if create ON) and map data for upload to XNAT
        for sd in dp.subjects:
            print('*****SubjectID:', sd)
            sd = str(sd)  # prevent unicode
            s = project.subject(sd)
            if not DEBUG and not s.exists():
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

            try:
                xsd = dp.getxsd()
                if isinstance(xsd, dict) and 'opex:cantabMOT' in list(xsd.values()):  # cantab
                    xsdtypes = xsd
                    for i, row in dp.subjects[sd].iterrows():
                        sampleid = dp.getSampleid(sd, row)
                        msg = 'SampleID: ' + sampleid
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
                            if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                                msg = self.loadSampledata(s, xsd, type + "_" + sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                            else:
                                print(xsd)
                                print(mandata)
                                print(data)


                # Extra filtering of nan
                elif 'dexa' in xsd:
                    for i, row in dp.subjects[sd].iterrows():
                        sampleid = dp.getSampleid(sd, row)
                        logging.debug('SampleID: ' + sampleid)
                        row.replace(nan, '', inplace=True)
                        (mandata, data) = dp.mapData(row, i, xsd)
                        if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                # Extract interval
                elif 'fitbit' in xsd:
                    for i, row in dp.subjects[sd].iterrows():
                        interval = int(row['interval'])
                        sampleid = dp.getSampleid(sd, interval)
                        logging.debug('SampleID: ' + sampleid)
                        (mandata, data) = dp.mapData(row, i)
                        if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                # Loop over each interval
                elif 'dass' in xsd:
                    maxmth = getMaxMth('dass')
                    intervals = list(range(0, maxmth + 1, 3))
                    intervals = detectTabs(dp, intervals)
                    for i in intervals:
                        iheaders = [c + "_" + str(i) for c in dp.fields]
                        sampleid = dp.getSampleid(sd, i)
                        logging.debug('SampleID: ' + sampleid)
                        row = dp.subjects[sd]
                        # row.replace(nan, '', inplace=True)
                        if iheaders[0] in row.columns:
                            if dp.validData(row[iheaders].values.tolist()[0]):
                                (mandata, data) = dp.mapData(row[iheaders], i, xsd)
                                if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                                    msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                    logging.info(msg)
                                    if 'created' in msg:
                                        print(msg)
                            else:
                                print('empty data - skipping')
                                continue

                # Validate data on entry at Timepoint intervals
                elif 'godin' in xsd or 'paces' in xsd or 'bpaq' in xsd:
                    row = dp.subjects[sd]
                    i = str(int(row['TimePoint']))
                    sampleid = dp.getSampleid(sd, i)
                    iheaders = dp.fields
                    if iheaders[0] in row.columns:
                        print('Sampleid:', sampleid)
                        if dp.validData(row[iheaders].values.tolist()[0]):
                            (mandata, data) = dp.mapData(row[iheaders], i, xsd)
                            if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                                msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                        else:
                            print('empty data - skipping')
                            continue

                # Static Interval of 0
                elif 'ipaq' in xsd:
                    interval = 0
                    sampleid = dp.getSampleid(sd, interval)
                    logging.debug('SampleID: ' + sampleid)
                    row = dp.subjects[sd]
                    if dp.validData(row.values.tolist()[0]):
                        print(sampleid)
                        (mandata, data) = dp.mapData(row, interval, xsd)
                        if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)

                # Loop for specified intervals
                elif 'acer' in xsd:
                    intervals = [0, 6]
                    iheaders = dp.fields
                    for i, row in dp.subjects[sd].iterrows():
                        sampleid = dp.getSampleid(sd, row)
                        logging.debug('SampleID: ' + sampleid)
                        if dp.validData(row[iheaders].values.tolist()):
                            (mandata, data) = dp.mapData(row, i, xsd)
                            if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                                msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)

                # Validate data with fields
                elif 'sf' in xsd:
                    iheaders = dp.fields
                    for i, row in dp.subjects[sd].iterrows():
                        # j = row['interval']
                        sampleid = dp.getSampleid(sd, row)
                        print('Sampleid:', sampleid)
                        if dp.validData(row[iheaders].values.tolist()):
                            (mandata, data) = dp.mapData(row, i, xsd)
                            if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                                msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                        else:
                            print('empty data - skipping')
                            continue

                # Only one row per subject
                elif 'insomnia' in xsd or 'psqi' in xsd:
                    i = dp.interval
                    sampleid = dp.getSampleid(sd, i)
                    print('Sample ID: ' + sampleid)
                    row = dp.subjects[sd]
                    # row.replace('nan', '', inplace=True)
                    if dp.validData(row[dp.fields].values.tolist()[0]):
                        (mandata, data) = dp.mapData(row, i, xsd)
                        if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)
                    else:
                        print('empty data - skipping')
                        continue


                # Specific filters required
                elif 'cosmed' in xsd:
                    for i, row in list(dp.subjects[sd].items()):
                        sampleid = dp.getSampleid(sd, i)
                        if sampleid in ['COS_1021LB_0', 'COS_1021LB_3']:
                            continue
                        logging.debug('SampleID: ' + sampleid)
                        (mandata, data) = dp.mapData(row, i, xsd)
                        if self.args.checks is None or not self.args.checks:  # Don't upload if checks
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
                    if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                        msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                        logging.info(msg)
                        if 'created' in msg:
                            print(msg)


                elif 'amunetall' in xsd:
                    sampleid = dp.getSampleid(sd)
                    logging.debug('SampleID: ' + sampleid)
                    (mandata, data) = dp.mapData()
                    print(mandata, data)
                    if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                        msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                        logging.info(msg)
                        print(msg)
                        if 'created' in msg:
                            print(msg)

                elif 'blood' in xsd:
                    for i, row in dp.subjects[sd].iterrows():
                        sampleid = dp.getPrefix() + "_" + dp.getSampleid(sd, row)
                        logging.debug('SampleID: ' + sampleid)
                        row.replace(nan, '', inplace=True)
                        (mandata, data) = dp.mapData(row, i, xsd)
                        if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)
                        else:
                            print(mandata)
                            print(data)

                # Single row per subject - no interval
                # elif ('adherence' in xsd) or ('ashsraw' in xsd) or ('ashslong2' in xsd) or ('ashslong3' in xsd):
                elif ('adherence' in xsd):
                    sampleid = dp.getSampleid(sd)
                    logging.debug('SampleID: ' + sampleid)
                    row = dp.subjects[sd]
                    (mandata, data) = dp.mapData(row)
                    if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                        msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                        logging.info(msg)
                        if 'created' in msg:
                            print(msg)

                # DEFAULT BASIC METHOD - No need to duplicate for each type
                else:
                    # elif 'food' in xsd or
                    #      'fcas' in xsd or
                    #      'accelday' in xsd or
                    #      'accelmonth' in xsd or
                    #      'taskret' in xsd or
                    #      'taskencode' in xsd or
                    if isinstance(xsd, dict) and hasattr(dp, 'etype') and dp.etype is not None:
                        xsd = xsd[dp.etype]
                    for i, row in dp.subjects[sd].iterrows():
                        sampleid = dp.getSampleid(sd, row)
                        logging.debug('SampleID: ' + sampleid)
                        (mandata, data) = dp.mapData(row, i, xsd)
                        if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                            msg = self.loadSampledata(s, xsd, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)
                        else:
                            print(xsd)
                            print(mandata)
                            print(data)

            except Exception as e:
                logging.error(e.args[0])
                raise ValueError(e)
        return (missing, matches)

    def runDataUpload(self, projectcode, inputdir, datatype):
        """
        *** Data parsing and upload for multiple data types ***
        Main method called by uploader and uploader_app

        :param projectcode: XNAT projectcode
        :param inputdir: Data directory containing xls or csv files
        :param datatype: as given by --expt in args or see opexconfig.db expts table -> option
        :return: success or error
        """
        msg = "Running data upload for %s from %s " % (datatype.upper(), inputdir)
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
                    if "RowBySession" in f2:
                        msg = "\nLoading: %s" % f2
                        print(msg)
                        logging.info(msg)
                        dp = CantabParser(f2, sheet, skip, header, etype)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)

            # ---------------------------------------------------------------------#
            elif datatype == 'adherence':

                # files = ['Training-Diary-AIT_20181123.xlsx', 'Training-Diary-MIT_20181123.xlsx',
                #          'Training-Diary-LIT_20181220.xlsx']  # TODO REMOVE HARD CODED FILES
                seriespattern = 'Training-Diary-*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                for f2 in files:
                    try:
                        print("Loading ", f2)
                        dp = AdherenceParser(f2)
                        (missing, matches) = self.uploadData(project, dp)
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2 + "_")

                    except Exception as e:
                        print("Cannot process file: %s" % e)
                        continue

            # ---------------------------------------------------------------------#
            elif datatype == 'amunetall':
                root_dir = inputdir
                interval_dir = ['1. 0M_Baseline', '2. 3M_Interim', '3. 6M_Post', '4. 9M_Maintenance', '5. 12M_Final']
                sheet = 0

                for i in interval_dir:
                    path = join(root_dir, i)
                    files = [f for f in listdir(path) if splitext(f)[-1] == '.zip' or splitext(f)[-1] == '.xml']
                    for f2 in files:
                        msg = "------------------------- STARTING: " + f2 + " -----------------------------"
                        logging.info(msg)
                        print(msg)
                        filetopath = join(path, f2)
                        try:
                            dp = AmunetParserXML(filetopath)
                            (missing, matches) = self.uploadData(project, dp)
                            # Output matches and missing
                            if len(matches) > 0 or len(missing) > 0:
                                (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir,
                                                                 f2 + "_" + str(sheet))
                        except Exception as e:
                            print("Cannot process file: %s" % e)
                            continue
            # ---------------------------------------------------------------------#
            elif datatype == 'sf':
                sheet = 0
                skip = 0
                etype = 'SF36'
                header = 0
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

            # ---------------------------------------------------------------------#
            elif datatype == 'food':
                sheet = 0
                skip = 1
                header = None
                seriespattern = '*.xlsx'
                etype = 'FOODDIARY'
                files = glob.glob(join(inputdir, seriespattern))
                for f2 in files:
                    print("Loading ", f2)
                    dp = FoodDiaryParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)

            # ---------------------------------------------------------------------#
            elif datatype == 'fcas':
                skip = 0
                seriespattern = '*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                sheet = 0

                for f2 in files:
                    print("Loading ", f2)
                    try:
                        dp = FcasParser(inputdir=inputdir, filename=f2)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir,
                                                             f2 + "_" + str(sheet))
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
                        print("Interval:", sheet)
                        dp = AcerParser(f2, sheet, skip, header, etype)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            reportfile = "%s_%d" % (basename(f2), sheet)
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, reportfile)


            # ---------------------------------------------------------------------#
            elif datatype in ['mridata', 'fmri', 'taskret', 'taskencode', 'mrifs', 'mriashs']:
                seriespattern = '*.xlsx'
                tabs = 1  # Number of tabs in xls to upload
                skip = 0
                header = None
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("Loading ", f2)
                    if datatype == 'mriashs':
                        etype = 'MRI ASHS'
                    elif datatype == 'mrifs':
                        etype = 'MRI FS'
                    elif datatype == 'taskret' or datatype == 'taskencode':
                        etype = datatype.upper()
                        tabs = 3  # Data upload file has 3 tabs: Bind, Bind3, Bind5
                    elif datatype == 'fmri':
                        etype = 'FMRI'
                    else:
                        raise ValueError("Cannot determine MRI datatype from %s" % datatype)
                    msg = "Running %s" % etype
                    print(msg)
                    for tab in range(tabs):
                        sheet = tab
                        dp = MridataParser(f2, sheet, skip, header, etype)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)

            # ---------------------------------------------------------------------#
            elif datatype == 'blood':
                seriespattern = '*.xlsx'
                # Set Excel sheet no
                sheet = 0
                # Skip x rows in Excel sheet before data
                skip = 0
                header = None
                if basename(inputdir) == 'CROSSOVER':
                    type = basename(dirname(inputdir))
                else:
                    type = basename(inputdir)  # assume dir is type eg COBAS to match
                # Change settings for some types
                if type == 'COBAS':
                    skip = 1
                elif type == 'ELISAS' or type == 'SOMATO':
                    sheet = 2

                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("\n****Loading ", f2)
                    dp = BloodParser(f2, sheet, skip, header, type=type)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)


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

            # ---------------------------------------------------------------------#
            elif datatype == 'dass':
                sheet = 0
                skip = 1
                header = None
                etype = 'DASS'
                seriespattern = '*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print("Loading ", f2)
                    dp = DassParser(f2, sheet, skip, header, etype)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)

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

            # ---------------------------------------------------------------------#
            elif datatype == 'godin':
                sheet = 0
                skip = 0
                header = 0
                etype = 'Godin'
                seriespattern = 'GODIN*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                maxmth = getMaxMth('godin')
                intervals = list(range(0, maxmth + 1, 3))
                for f2 in files:
                    print("Loading ", f2)
                    intervals = detectTabs(f2, intervals)
                    for sheet in range(0, len(intervals)):
                        i = intervals[sheet]
                        print('Interval:', i)
                        try:
                            dp = GodinParser(f2, sheet, skip, header, etype)
                            dp.interval = i
                            (missing, matches) = self.uploadData(project, dp)
                            # Output matches and missing
                            if len(matches) > 0 or len(missing) > 0:
                                reportfile = "%s_%d" % (basename(f2), i)
                                (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, reportfile)
                        except ValueError as e:
                            logging.warning(e)
                            continue


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
                            reportfile = "%s_%s" % (basename(f2), str(i))
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, reportfile)

            # ---------------------------------------------------------------------#
            elif datatype == 'missing':  # TODO Move to a separate file - not available as option in GUI
                seriespattern = '*.xlsx'
                etype = 'MISS'
                files = glob.glob(join(inputdir, seriespattern))
                for f2 in files:
                    print("Loading ", f2)
                    try:
                        dp = MissingParser(datafile=f2)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                    except ValueError as e:
                        logging.warning(e)
                        continue

            # ---------------------------------------------------------------------#
            elif datatype == 'psqi':
                skip = 1
                header = 1
                etype = 'PSQI'
                seriespattern = 'PSQI*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                maxmth = getMaxMth('psqi')
                intervals = list(range(0, maxmth + 1, 3))
                for f2 in files:
                    print("Loading ", f2)
                    intervals = detectTabs(f2, intervals)
                    for sheet in range(0, len(intervals)):
                        i = intervals[sheet]
                        print('Interval:', i)
                        try:
                            dp = PsqiParser(f2, sheet, skip, header, etype)
                            dp.interval = i
                            (missing, matches) = self.uploadData(project, dp)
                            # Output matches and missing
                            if len(matches) > 0 or len(missing) > 0:
                                reportfile = "%s_%d" % (basename(f2), i)
                                (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, reportfile)
                        except ValueError as e:
                            logging.warning(e)
                            continue


            # ---------------------------------------------------------------------#
            elif datatype == 'insomnia':
                skip = 0
                header = None
                etype = 'Insomnia'
                seriespattern = 'ISI*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                maxmth = getMaxMth('insomnia')
                intervals = list(range(0, maxmth + 1, 3))
                for f2 in files:
                    print("Loading ", f2)
                    intervals = detectTabs(f2, intervals)
                    for sheet in range(0, len(intervals)):
                        i = intervals[sheet]
                        print('Interval:', i)
                        try:
                            dp = InsomniaParser(f2, sheet, skip, header, etype)
                            dp.interval = i
                            (missing, matches) = self.uploadData(project, dp)
                            # Output matches and missing
                            if len(matches) > 0 or len(missing) > 0:
                                reportfile = "%s_%d" % (basename(f2), i)
                                (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, reportfile)
                        except ValueError as e:
                            logging.warning(e)
                            continue

            # ---------------------------------------------------------------------#
            elif datatype == 'cosmed':
                try:
                    if sys.platform == 'win32':
                        pathsfile = join(inputdir, 'xnatpaths1.txt')
                    else:
                        pathsfile = join(inputdir, 'xnatpaths_mac.txt')

                    f = open(pathsfile)
                    paths = {}
                    for p in f.readlines():
                        p = p.rstrip()
                        (k, v) = p.split('=')
                        paths[k] = v
                    inputsubdir = join(paths['datadir'], paths['subdata'])
                    datafile = join(paths['datadir'], paths['datafile'])
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
                        matches = list(dp.expts.keys())
                        for eid in list(dp.expts.keys()):
                            print(eid, dp.expts.get(eid))
                    else:
                        (missing, matches) = dp.uploadDates(projectcode, self.xnat)
                except Exception as e:
                    raise ValueError(e)
            # ---------------------------------------------------------------------#
            elif datatype == 'mri':
                if hasattr(self.args, 'opexid'):
                    opexid = self.args.opexid
                else:
                    opexid = False
                if hasattr(self.args, 'subjectchars'):
                    snum = self.args.subjectchars
                else:
                    snum = 6
                fid = self.xnat.upload_MRIscans(projectcode, inputdir, opexid, snum)
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
    runoption = args.expt
    rundir = args.exptdata
    projectcode = args.projectcode

    try:
        if not DEBUG:
            if uploader.xnat.testconnection():
                print("Connected")
                # Check project code is correct
                projectcode = uploader.args.projectcode
                p = uploader.xnat.get_project(projectcode)
                # Test run
                missing = []
                matches = []
                if not p.exists():
                    msg = "This project [%s] does not exist in this database [%s]" % (
                        projectcode, uploader.args.database)
                    raise ConnectionError(msg)
                # List available subjects in project
                if uploader.args.subjects is not None and uploader.args.subjects:
                    msg = "Calling List Subjects"
                    print(msg)
                    uploader.xnat.list_subjects_all(projectcode)
                # List available projects
                if uploader.args.projects is not None and uploader.args.projects:
                    print("Calling List Projects")
                    projlist = uploader.xnat.list_projects()
                    for p in projlist:
                        print("Project: ", p.id())

            else:
                raise ConnectionError("Connection failed - check config")
        ################ Upload expt data ################
        uploader.runDataUpload(projectcode, rundir, runoption)

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
