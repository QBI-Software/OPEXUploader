from __future__ import print_function

# -*- coding: utf-8 -*-
"""
XNAT Utility script: Upload scans via subject label (not XNAT id)
where scans are loaded from structure as follows:
/project_id/subject_label/scans/group/session_type/

DICOM FILE FORMATS: dcm or Siemens IMA
Created on Thu Feb 23 10:58:21 2017

@author: Liz Cooper-Williams, QBI
"""
import ConfigParser
import argparse
import csv
import glob
import logging
import os
import shutil
import warnings
from os import listdir
from os.path import expanduser
from os.path import isdir, join

import dicom
import pyxnat

warnings.filterwarnings("ignore")
DEBUG = 1


class XnatConnector:
    def __init__(self, configfile, sitename):
        config = ConfigParser.RawConfigParser()
        config.read(configfile)
        self.url = config.get(sitename, "URL")
        self.user = config.get(sitename, "USER")
        self.passwd = config.get(sitename, "PASS")
        # print "Config:", self.url , ", ", self.user, ", ", self.passwd

    def connect(self):
        """
        Connect to xnat server via config
        """
        self.conn = pyxnat.Interface(server=self.url, user=self.user, verify=True,
                                     password=self.passwd, cachedir='/tmp')  # connection object

    def get_project(self, projectcode):
        if not self.conn:
            self.connect()
        qry_project = '/projects/%s' % projectcode
        return self.conn.select(qry_project)

    def get_projectPI(self, projectcode):
        """
        Finds the Principal Investigator for the project and returns their surname
        :param projectcode:
        :return:
        """
        if not self.conn:
            self.connect()
        qry_project = '/projects/%s' % projectcode
        proj = self.conn.select(qry_project)
        return proj.attrs.get('xnat:projectData/PI/lastname')

    def get_subjects(self, projectcode):
        if not self.conn:
            self.connect()
        qry = '/projects/%s/subjects' % projectcode
        return self.conn.select(qry)

    def list_projects(self):
        if not self.conn:
            self.connect()
        qry_project = '/projects'
        return self.conn.select(qry_project)

    def list_subjects_all(self, projectcode):
        """
        Lists all subjects in a project to console
        """

        subj = self.get_subjects(projectcode)
        outfilename = projectcode + 'subjectlist.csv'
        with open(outfilename, 'wb') as csvfile:
            fieldnames = ['ID', 'subject_ID']
            mywriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
            mywriter.writeheader()
            for s in subj:
                print("ID=", s.label(), ",SubjectID=", s.id())  # xnat subject id eg XNAT_S00006
                mywriter.writerow({'ID': s.label(), 'subject_ID': s.id()})
        return outfilename

    def get_subjectid_bylabel(self, projectcode, label):
        """
        Find the XNAT ID for a subject by label
        
        EXAMPLE
        sid = ixnat.get_subjectid_bylabel('QBICC', '1554603')
        
        """
        # constraints = [('xnat:subjectData/LABEL', '=', label)]
        project = self.get_project(projectcode)
        s = project.subject(label)
        if s.exists():
            return s.id()
        else:
            logging.warning("Subject not found: %s", label)
            return None

    def checkUniqueLabel(self, subject, label):
        prefix = label.rsplit('_', 1)[0]
        experiments = [e.label() for e in subject.experiments() if
                       e.datatype() == 'xnat:mrSessionData' and e.label().startswith(prefix)]
        if label in experiments:
            experiments.sort(reverse=True)
            ctr = experiments[0].rsplit('_', 1)[1]
            # prefix = experiments[0].rsplit('_', 1)[0]
            c = int(ctr) + 1
            label = prefix + "_" + str(c)
        return label

    def upload_MRIscans(self, projectcode, scandir):
        """
        Upload MRI scans from scandir to project
        :param projectcode: XNAT ID for project eg QBICC
        :param scandir: full path name of dir containing subdirs with data
        eg /ibscratch/irc5scans/data
        data should be organized by DICOM series as: data/subject_label/scans/series_number/*.dcm (or *.IMA)
        :return: number of sessions loaded
        """
        project = self.get_project(projectcode)
        owners = project.owners()
        proj_pi = self.get_projectPI(projectcode)
        ctr = 0
        default_scantype = 'MR Image Storage'
        scanfiles = [f for f in listdir(scandir) if os.path.isdir(join(scandir, f))]
        if scanfiles:
            dirpath = os.path.dirname(scandir)
            donepath = join(dirpath, 'done')
            if not os.path.isdir(donepath):
                try:
                    os.mkdir(donepath)
                except:
                    raise OSError

        for slabel in scanfiles:
            sid = self.get_subjectid_bylabel(projectcode, slabel)
            if sid is None:
                logging.warning("Subject doesn't exist - skipping %s", slabel)
                continue
            s = project.subject(sid)

            if s.exists():
                ctr = ctr + 1
                # Set experiment
                elabel = 'MR_%s_%d' % (s.label(), ctr)
                elabel = self.checkUniqueLabel(s, elabel)  # eid = self.find_next_experimentID(projectcode, prefix,True)
                message = "Uploading scans for %s: %s with expt=%s" % (s.id(), s.label(), elabel)
                logging.info(message)
                print(message)
                expt = s.experiment(elabel)
                expt.create()  # experiments='xnat:mrSessionData')
                uploaddir = join(scandir, slabel, 'scans')
                scan_ctr = 0
                # (scan_date, scan_time) = (None, None)
                others = {}
                for subdr in listdir(uploaddir):
                    dcm_path = join(uploaddir, subdr)
                    scan_files = glob.glob(join(dcm_path, '*.*'))
                    if len(scan_files) == 0:  # check this isn't wrong dir
                        logging.warning("File directory doesn't contain dcm files:%s", uploaddir)
                        continue

                    scan_type = self.getScanType(default_scantype, scan_files[0])
                    scan_id = self.getSeriesNumber(subdr, scan_files[0])
                    print('Scan ID: %s  Scan type=%s' % (scan_id, scan_type))

                    scan_pi = self.getPI(scan_files[0])
                    if DEBUG or proj_pi in scan_pi or proj_pi in owners:
                        logging.info("Owner verified:  scan=%s project=%s", scan_pi, proj_pi)
                    else:
                        logging.warning("Owner does not match - skipping upload: scan=%s project=", scan_pi, proj_pi)
                        continue
                    # (scan_date, scan_time) = self.getSeriesDatestamp(scan_files[0])
                    scan_ctr += 1
                    scan = expt.scan(str(scan_id))
                    # scan.insert() #Should detect type BUT IT DOESN'T
                    if scan_type == 'MR Image Storage':
                        scan.create(scans='xnat:mrScanData')
                    elif scan_type == 'Secondary Capture Image Storage':
                        scan.create(scans='xnat:scScanData')
                    else:
                        modality = self.getModality(scan_files[0])
                        if modality is not None and modality == 'MR':
                            scan.create(scans='xnat:otherDicomScanData')

                    dicom_resource = scan.resource('DICOM')  # crucial for display DICOM headers
                    dicom_resource.put_dir(dcm_path, overwrite=True, extract=True)
                    # Update per scan doesn't work:
                    ## hdrs = '/REST/experiments/%s/scans/%s?pullDataFromHeaders=true' % (elabel, str(scan_id))
                    # xnat.conn.put(hdrs)

                # Update headers after files uploaded (mrScan only)
                if expt.scans():
                    # expt.trigger(fix_types=True, scan_headers=True, pipelines=True) - doesn't work properly as calls are in wrong order so list each function as below
                    try:
                        expt.pull_data_from_headers()
                    except:
                        message = "Unable to extract header data from this xsi type: %s" % scan_type
                        logging.warning(message)
                    expt.fix_scan_types()
                    expt.trigger_pipelines()
                    # mark or move folder if done
                    if donepath:
                        try:
                            shutil.move(join(scandir, slabel), donepath)
                            message = "Uploaded scans moved to %s" % donepath
                            logging.info(message)
                            print(message)
                        except IOError:
                            message = "Error in moving uploaded scans to %s" % donepath
                            logging.warning(message)
                            print(message)

            else:
                logging.warning("Subject doesn't exist in this project: %s %s", projectcode, sid)

        return ctr

    def getScanType(self, dirlabel, dicomfile):
        type = dirlabel
        dcm = dicom.read_file(dicomfile)
        if dcm:
            type = dcm.SOPClassUID

        return type

    def getModality(self, dicomfile):
        type = None
        dcm = dicom.read_file(dicomfile)
        if dcm:
            type = dcm.Modality

        return type

    def getSeriesNumber(self, dirlabel, dicomfile):
        series = dirlabel
        dcm = dicom.read_file(dicomfile)
        if dcm:
            series = dcm.SeriesNumber

        return series

    def getSeriesDatestamp(self, dicomfile):
        sdate = None
        stime = None
        dcm = dicom.read_file(dicomfile)
        if dcm:
            sdate = dcm.SeriesDate
            stime = dcm.SeriesTime

        return (sdate, stime)

    def getPI(self, dicomfile):
        pi = None
        dcm = dicom.read_file(dicomfile)
        if dcm:
            pi = dcm.RequestedProcedureDescription  # check this field is set with Principal Investigator
        return pi


# =============================================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='XnatUploadScans',
                                     description='''\
        Script for uploading scans to QBI XNAT db
         ''')
    parser.add_argument('database', action='store',
                        help='select database config from xnat.cfg to connect to [qbixnat|irc5xnat]')
    parser.add_argument('projectcode', action='store', help='select project by code eg QBICC')
    parser.add_argument('--p', action='store_true', help='list projects')
    parser.add_argument('--s', action='store_true', help='list subjects')
    parser.add_argument('--g', action='store', help='get XNAT ID for subject ID')
    parser.add_argument('--c', action='store', help='database configuration file (overrides ~/.xnat.cfg)')
    parser.add_argument('--u', action='store',
                        help='Upload MRI scans from directory as data/subject_label/scans/session_label/[*.dcm|*.IMA]')

    args = parser.parse_args()

    # get current user's login details (linux) or local file (windows)
    home = expanduser("~")
    configfile = join(home, '.xnat.cfg')
    logfile = join(home, 'logs', 'xnatuploadscans.log')
    if args.c is not None:
        try:
            if os.access(args.c, os.R_OK):
                configfile = args.c
            if not os.access(join(home, 'logs'), os.R_OK):
                os.mkdir(join(home, 'logs'))

        except:
            raise IOError
    try:
        os.access(configfile, os.R_OK)
    except:
        raise os.error

    logging.basicConfig(filename=logfile, level=logging.INFO, format='%(asctime)s %(message)s',
                        datefmt='%d-%m-%Y %I:%M:%S %p')
    logging.info('Connected to Server:%s Project:%s', args.database, args.projectcode)
    xnat = XnatConnector(configfile, args.database)
    xnat.connect()
    if (xnat.conn):
        logging.info("...Connected")
        print("Connected")

        projectcode = args.projectcode
        if (args.s is not None and args.s):
            logging.info("Calling List Subjects")
            xnat.list_subjects_all(projectcode)

        if (args.p is not None and args.p):
            logging.info("Calling List Projects")
            projlist = xnat.list_projects()
            for p in projlist:
                print("Project: ", p.id())
        if (args.g is not None and args.g):
            subjectid = args.g
            sid = xnat.get_subjectid_bylabel(projectcode, subjectid)
            print("XNAT ID=%s for subject ID=%s" % (sid, subjectid))
        if (args.u is not None and args.u):
            uploaddir = args.u  # Top level DIR FOR SCANS
            # Directory structure data/subject_label/scans/session_id/*.dcm
            if isdir(uploaddir):
                fid = xnat.upload_MRIscans(projectcode, uploaddir)
                if fid == 0:
                    logging.warning('Upload not successful - 0 sessions uploaded')
                else:
                    logging.info("Subject sessions uploaded: %d", fid)
            else:
                logging.warning("Directory path cannot be found: %s", uploaddir)

        xnat.conn.disconnect()
        logging.info("Complete")
        print("FINISHED - see xnatuploadscans.log for details")

    else:
        logging.warning("Failed to connect")
