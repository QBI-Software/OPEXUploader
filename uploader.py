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
__version__ = '1.2.0'
__author__ = 'Liz Cooper-Williams'

import argparse
import csv
import glob
import logging
import re
import shutil
from datetime import date
from os import R_OK, access, listdir, getcwd, mkdir
from os.path import expanduser, isdir, join, basename, split, exists

from numpy import isnan, nan

from requests.exceptions import ConnectionError

from dataparser.AcerParser import AcerParser
from dataparser.AmunetParser import AmunetParser,generateAmunetdates
from dataparser.BloodParser import BloodParser
from dataparser.CantabParser import CantabParser
from dataparser.CosmedParser import CosmedParser
from dataparser.DexaParser import DexaParser
from dataparser.MridataParser import MridataParser
from dataparser.VisitParser import VisitParser
from dataparser.DassParser import DassParser
from xnatconnect.XnatConnector import XnatConnector


class OPEXUploader():
    def __init__(self, args):
        logfile=join(expanduser('~'),'logs','xnatupload.log')
        logdir = split(logfile)[0]
        if not access(logdir, R_OK):
            mkdir(logdir)
        logging.basicConfig(filename=logfile, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%d-%m-%Y %I:%M:%S %p')
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
        self.xnat.connect()

    def xnatdisconnect(self):
        self.xnat.conn.disconnect()

    # ------------------------------------------------------------------------------------
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
            sids = self.xnat.get_subjects(projectcode)
            for m in missing:
                rootid = m['ID'][0:4]
                guess = [s.label() for s in sids if rootid in s.label()]
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

        msg = "%sMatched participants: %d\nMissing participants: %d\n" % (
            msg, len(matches), len(missing))
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
    #------------------------------------------------------------------------------------
    def uploadData(self, project, dp):
        """
        Upload data via specific Data parser
        :param dp:
        :return: missing and matches
        """
        missing = []
        matches = []
        if len(dp.subjects) <=0:
            dp.sortSubjects()
        for sd in dp.subjects:
            print '*****SubjectID:', sd
            s = project.subject(sd)
            if not s.exists():
                if self.args.create is not None and self.args.create:
                    # create subject in database
                    skwargs = dp.getSubjectData(sd)
                    s = self.xnat.createSubject(projectcode, sd, skwargs)
                    logging.info('Subject created: ' + sd)
                    print('Subject created: ' + sd)
                else:
                    missing.append({"ID": sd, "rows": dp.subjects[sd]})
                    msg = 'Subject does not exist - skipping: %s' % sd
                    print msg
                    logging.warning(msg)
                    continue
            # Load data PER ROW
            matches.append(sd)
            if self.args.checks is None or not self.args.checks:  # Don't upload if checks
                try:
                    xsdtypes = dp.getxsd()
                    if 'dexa' in xsdtypes:
                        checkfield = dp.fields['Field'][0]  # test if data in row
                        for i, row in dp.subjects[sd].items():
                            if checkfield in row and not isnan(row[checkfield].iloc[0]):
                                print 'Interval:', dp.intervals[i]
                                sampleid = dp.getSampleid(sd, i)
                                (mandata, data) = dp.mapData(row, i, xsdtypes)
                                msg = self.loadSampledata(s, xsdtypes, sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                    elif 'dass' in xsdtypes:
                        intervals = range(0, 13, 3)
                        for i in intervals:
                            iheaders = [c + "_" + str(i) for c in dp.fields]
                            sampleid = dp.getSampleid(sd, i)
                            row = dp.subjects[sd]
                            if dp.validData(row[iheaders].values.tolist()[0]):
                                (mandata, data) = dp.mapData(row[iheaders], i, xsdtypes)
                                msg = self.loadSampledata(s, xsdtypes, sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                    elif 'cosmed' in xsdtypes:
                        for i, row in dp.subjects[sd].items():
                            row.replace(nan, '', inplace=True)
                            sampleid = dp.getSampleid(sd, i)
                            if sampleid in ['COS_1021LB_0', 'COS_1021LB_3']:
                                continue
                            (mandata, data) = dp.mapData(row, i, xsdtypes)

                            msg = self.loadSampledata(s, xsdtypes, sampleid, mandata, data)
                            logging.info(msg)
                            if 'created' in msg:
                                print(msg)
                    else:
                        for i, row in dp.subjects[sd].iterrows():
                            sampleid = dp.getSampleid(sd, row)
                            row.replace(nan, '', inplace=True)

                            if ('amunet' in xsdtypes):
                                msg = self.loadAMUNETdata(sampleid, i, row, s, dp)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                            elif ('FS' in xsdtypes or 'COBAS' in xsdtypes):
                                xsd = dp.getxsd()[dp.type]
                                (mandata, data) = dp.mapData(row, i, xsd)
                                # print mandata
                                # print data
                                if hasattr(dp,'opex'):
                                    p = dp.opex['prefix'][dp.opex['xsitype'] == xsd] #Series
                                    prefix = p.values[0]
                                else:
                                    prefix = dp.type
                                msg = self.loadSampledata(s, xsd, prefix + "_" + sampleid, mandata, data)
                                logging.info(msg)
                                if 'created' in msg:
                                    print(msg)
                            else:  # cantab
                                if  ('NOT_RUN' in row.values) or ('ABORTED' in row.values):
                                    msg = "Skipping due to ABORT or NOT RUN: %s" % sampleid
                                    logging.warning(msg)
                                    print(msg)
                                    continue
                                for type in xsdtypes.keys():
                                    (mandata, data) = dp.mapData(row, i, type)
                                    xsd = xsdtypes[type]
                                    msg = self.loadSampledata(s, xsd, type + "_" + sampleid, mandata, data)
                                    logging.info(msg)
                                    if 'created' in msg:
                                        print(msg)
                except Exception as e:
                    logging.error(e.args[0])
                    raise ValueError(e)
        return (missing, matches)

    def runDataUpload(self, projectcode,inputdir,datatype):
        """
        Data upload template
        :param projectcode:
        :param inputdir:
        :param kwargs:
        :return: success or error
        """
        msg = "Running data upload for %s from %s " % (datatype, inputdir)
        logging.info(msg)
        print msg
        project = self.xnat.get_project(projectcode)
        if access(inputdir, R_OK):
            if datatype == 'cantab':
                seriespattern = '*.csv'
                sheet = 0
                fields = join(getcwd(), "resources", 'cantab_fields.csv')
                files = glob.glob(join(inputdir, seriespattern))
                print "Files:", len(files)
                for f2 in files:
                    if ("RowBySession" in f2):
                        msg = "\nLoading: %s" % f2
                        print msg
                        logging.info(msg)
                        dp = CantabParser(fields, f2, sheet)
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)
            #---------------------------------------------------------------------#
            elif datatype == 'amunet':
                sheet = 0
                topinputdir = inputdir
                basedatesfile = 'amunet_participantdates.csv'
                seriespattern = '*.xlsx'
                subdirs = listdir(topinputdir)
                print 'Finding dates from subdirectories'
                for inputdir in subdirs:
                    if inputdir not in ['0m', '3m', '6m', '9m', '12m']:
                        continue
                    interval = inputdir[0]
                    inputdir = join(topinputdir, inputdir)
                    print inputdir
                    # Get dates from zip files
                    dates_uri_file = join(inputdir, 'folderpath.txt')
                    with open(dates_uri_file, "r") as dd:
                        content = dd.readlines()
                        for line in content:
                            dates_uri = line.strip()
                            break
                    if len(dates_uri) <= 0:
                        raise ValueError('No dates file found - exiting')
                    dates_csv = generateAmunetdates(dates_uri, basedatesfile, interval)
                    # copy file to this dir
                    shutil.copyfile(dates_csv, join(inputdir, basename(dates_csv)))
                    # Get xls files
                    files = glob.glob(join(inputdir, seriespattern))
                    print("Loading Files:", len(files))
                    for f2 in files:
                        print("Loading", f2)
                        dp = AmunetParser(f2, sheet, ival=interval)
                        #dp.interval = interval
                        (missing, matches) = self.uploadData(project, dp)
                        # Output matches and missing
                        if len(matches) > 0 or len(missing) > 0:
                            (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                            msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                            print(msg)
                            logging.info(msg)

            # ---------------------------------------------------------------------#
            elif datatype == 'acer':
                sheet = 1  # "1"
                seriespattern = '*.*'
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print "Loading ", f2
                    dp = AcerParser(f2, sheet)
                    (missing, matches) = self.uploadData(project, dp)
                    # Output matches and missing
                    if len(matches) > 0 or len(missing) > 0:
                        (out1, out2) = self.outputChecks(projectcode, matches, missing, inputdir, f2)
                        msg = "Reports created: \n\t%s\n\t%s" % (out1, out2)
                        print(msg)
                        logging.info(msg)
            # ---------------------------------------------------------------------#
            elif datatype == 'mridata':
                seriespattern = '*.csv'
                sheet = 1  # "1"
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print "Loading ", f2
                    dp = MridataParser(f2, sheet)
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
                skip = 1
                type = basename(inputdir)  # assume dir is type eg COBAS to match

                if type == 'MULTIPLEX':
                    skip = 0
                files = glob.glob(join(inputdir, seriespattern))
                print("Files:", len(files))
                for f2 in files:
                    print "Loading ", f2
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
                skip = 4
                fields = join(getcwd(), "resources", "dexa_fields.xlsx")
                seriespattern = 'DXA Data entry*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print "Files:", len(files)
                for f2 in files:
                    print "Loading ", f2
                    dp = DexaParser(fields, f2, sheet, skip)
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
                skip = 0
                header = 2
                seriespattern = 'DASS Data entry*.xlsx'
                files = glob.glob(join(inputdir, seriespattern))
                print "Files:", len(files)
                for f2 in files:
                    print "Loading ", f2
                    dp = DassParser(f2, sheet, skip, header)
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
                    f = open(join(inputdir, 'xnatpaths.txt'))
                    paths ={}
                    for p in f.readlines():
                        p = p.rstrip()
                        (k,v) = p.split('=')
                        paths[k] = v
                    inputsubdir = join(paths['datadir'],paths['subdata'])
                    datafile = join(paths['datadir'],paths['datafile'])  # 'VO2data_VEVCO2_20171009.xlsx'
                    msg = 'COSMED: Datafile= %s \nTime series for files in %s ' % (datafile, inputsubdir )
                    logging.info(msg)
                    print msg

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
                inputfile = join(inputdir,'Visits.xlsx')
                try:
                    dp = VisitParser(inputfile, 0, 1)
                    dp.processData()
                    if self.args.checks:
                        print "**UPDATING dates**"
                        for eid in dp.expts.keys():
                            print eid, ": ", dp.expts.get(eid)
                    else:
                        dp.uploadDates(projectcode, self.xnat)
                except Exception as e:
                    raise ValueError(e)

        else:
            msg = "Input directory error: %s" % inputdir
            logging.error(msg)
            raise IOError(msg)


########################################################################
if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='OPEX Uploader',
                                     description='''\
        Script for uploading scans and sample data to QBI OPEX XNAT db
         ''')
    parser.add_argument('database', action='store', help='select database config from xnat.cfg to connect to')
    parser.add_argument('projectcode', action='store', help='select project by code')
    #optional
    parser.add_argument('--projects', action='store_true', help='list projects')
    parser.add_argument('--subjects', action='store_true', help='list subjects')
    parser.add_argument('--config', action='store', help='database configuration file (overrides ~/.xnat.cfg)')
    parser.add_argument('--cantab', action='store', help='Upload CANTAB data from directory')
    parser.add_argument('--checks', action='store_true', help='Test run with output to files')
    parser.add_argument('--update', action='store_true', help='Also update existing data')
    #parser.add_argument('--skiprows', action='store_true', help='Skip rows in CANTAB data if NOT_RUN or ABORTED')
    parser.add_argument('--amunet', action='store', help='Upload Water Maze (Amunet) data from directory')
    parser.add_argument('--amunetdates', action='store', help='Extract date info from orig files in this dir')
    parser.add_argument('--acer', action='store', help='Upload ACER data from directory')
    parser.add_argument('--blood', action='store', help='Upload BLOOD data from directory')
    parser.add_argument('--create', action='store_true', help='Create Subject from input data if not exists')
    parser.add_argument('--mridata', action='store',
                        help='Upload MRI data from directory - detects ASHS or FreeSurf from filename')
    parser.add_argument('--mri', action='store',
                        help='Upload MRI scans from directory with data/subject_label/scans/session_label/[*.dcm|*.IMA]')
    parser.add_argument('--dexa', action='store', help='Upload DEXA data from directory')
    parser.add_argument('--dass', action='store', help='Upload DASS data from directory')
    parser.add_argument('--cosmed', action='store', help='Upload COSMED data from directory')
    parser.add_argument('--visit', action='store', help='Update visit dates',
                        default='sampledata\\visit\\Visits_genders.xlsx')

    args = parser.parse_args()
    uploader = OPEXUploader(args)
    uploader.config()
    uploader.xnatconnect()
    logging.info('Connecting to Server:%s Project:%s', uploader.args.database, uploader.args.projectcode)

    try:
        if uploader.xnat.testconnection():
            logging.info("...Connected")
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
                print msg
                logging.info(msg)
                uploader.xnat.list_subjects_all(projectcode)
            # List available projects
            if (uploader.args.projects is not None and uploader.args.projects):
                logging.info("Calling List Projects")
                projlist = uploader.xnat.list_projects()
                for p in projlist:
                    print("Project: ", p.id())
            # Upload MRI scans from directory
            if (uploader.args.mri is not None and uploader.args.mri):
                uploaddir = uploader.args.mri  # Top level DIR FOR SCANS
                # Directory structure data/subject_label/scans/session_id/*.dcm
                if isdir(uploaddir):
                    fid = uploader.xnat.upload_MRIscans(projectcode, uploaddir, opexid=True)
                    if fid == 0:
                        msg = 'Upload not successful - 0 sessions uploaded'
                        raise ValueError(msg)
                    else:
                        logging.info("Subject sessions uploaded: %d", fid)
                else:
                    msg = "Directory path cannot be found: %s" % uploaddir
                    raise IOError(msg)

            # Upload CANTAB data from directory
            if (uploader.args.cantab is not None and uploader.args.cantab):
                uploader.runDataUpload(projectcode, uploader.args.cantab,'cantab')

            ### Upload Amunet data from directory
            # Files are in 2 parts and do not contain interval or visit date so should be separated into folders:
            # 0m, 3m, 6m, 9m
            # Dates are generated separately below from the raw folders - path given in "folderpath.txt"
            # csv files with dates should be placed in the same directory to be loaded with sortSubjects
            if (uploader.args.amunet is not None and uploader.args.amunet):
                uploader.runDataUpload(projectcode, uploader.args.amunet, 'amunet')
            #------------------------------------------------------------------------------------
            ### Upload ACE-R data from directory
            if (uploader.args.acer is not None and uploader.args.acer):
                uploader.runDataUpload(projectcode, uploader.args.acer, 'acer')

            # Upload MRI data analysis from directory
            if (uploader.args.mridata is not None and uploader.args.mridata):
                uploader.runDataUpload(projectcode, uploader.args.mridata, 'mridata')

            # Upload BLOOD data from directory
            if (uploader.args.blood is not None and uploader.args.blood):
                uploader.runDataUpload(projectcode, uploader.args.blood, 'blood')

            # Upload DEXA data from directory
            if (uploader.args.dexa is not None and uploader.args.dexa):
                uploader.runDataUpload(projectcode, uploader.args.dexa, 'dexa')
            # Upload DASS data from directory
            if (uploader.args.dass is not None and uploader.args.dass):
                uploader.runDataUpload(projectcode, uploader.args.dass, 'dass')

            # Upload COSMED data from directory
            if (uploader.args.cosmed is not None and uploader.args.cosmed):
                uploader.runDataUpload(projectcode, uploader.args.cosmed, 'cosmed')

            # Update dates for data not containing visit date
            if (uploader.args.visit is not None and uploader.args.visit):
                uploader.runDataUpload(projectcode, uploader.args.visit, 'visit')

        else:
            raise ConnectionError("Connection failed - check config")
    except IOError as e:
        logging.error(e)
        print "Failed IO:", e
    except ConnectionError as e:
        logging.error(e)
        print "Failed connection:", e
    except ValueError as e:
        logging.error(e)
        print "ValueError:", e
    except Exception as e:
        logging.error(e)
        print "ERROR:", e
    finally:  # Processing complete
        uploader.xnatdisconnect()
        logging.info("FINISHED")
        print "\n****FINISHED**** - see xnatupload.log for details"
