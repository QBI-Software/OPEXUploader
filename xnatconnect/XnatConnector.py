# -*- coding: utf-8 -*-
"""
XNAT connector class for scripts

@author: Liz Cooper-Williams, QBI
"""
import argparse
import csv
import glob
import logging
import os
import shutil
import warnings
from os import listdir
from os.path import expanduser
from os.path import join
import multiprocessing
#import resource
from itertools import repeat
import datetime
import time
import dicom
import pyxnat
import pandas as pd
from configobj import ConfigObj

warnings.filterwarnings("ignore")
DEBUG = 1
VERBOSE = 0

class XnatConnector:
    def __init__(self, configfile, sitename):
        config = ConfigObj(configfile)
        self.url = config[sitename]['URL']
        self.user = config[sitename]['USER']
        self.passwd = config[sitename]['PASS']
        # print "Config:", self.url , ", ", self.user, ", ", self.passwd

    def connect(self):
        """
        Connect to xnat server via config
        """
        self.conn = pyxnat.Interface(server=self.url, user=self.user, verify=True,
                                     password=self.passwd, cachedir='/tmp')  # connection object

    def testconnection(self):
        """
        Test connection actually exists by returning some data
        :return: true or false
        """
        testconn = self.conn.inspect.datatypes('xnat:subjectData')
        return (len(testconn) > 0)

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

    def list_subjects_all(self, projectcode, fieldnames=None):
        """
        Lists all subjects in a project to console
        """

        subj = self.get_subjects(projectcode)
        outfilename = projectcode + '_subjectlist.csv'
        with open(outfilename, 'wb') as csvfile:
            if fieldnames is None:
                fieldnames = ['ID','group','label','dob','gender','handedness','education']
            mywriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
            mywriter.writeheader()
            for s in subj:
                if VERBOSE:
                    print "ID=", s.label(), ", SubjectID=", s.id() # xnat subject id eg XNAT_S00006
                #ID	group	label	dob	gender	handedness	education
                mywriter.writerow({'ID': s.label(),
                                   'group': s.attrs.get('group'),
                                   'dob': s.attrs.get('dob'),
                                   'gender': s.attrs.get('gender'),
                                   'handedness': s.attrs.get('handedness'),
                                   'education': s.attrs.get('education')
                                   })
        print "Subjects written to file:", outfilename
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

    def createSubject(self,projectcode,label, subjectkwargs):
        """
        Create a subject in this project with the label as ID and subject parameters as key value
        No checks made on args eg {'dob': '1949-11-06', 'gender': 'female'}
        """
        project = self.get_project(projectcode)
        subject = project.subject(label)
        subject.create()
        if subject.exists():
            #set attrs
            subject.attrs.mset(subjectkwargs)
            return subject
        else:
            logging.warning("Subject not created: %s", label)
            return None

    def createExperiment(self,subject,xsdtype,exptid,mandata,exptdata):
        """
        Creates an experiment of type xsdtype for subject with exptid and exptdata as dict
        No checks made for correct data fields - must represent the XSD as set in the database
        :param subject: Subject object
        :param xsdtype: schema datatype
        :param exptid: ID for expt
        :param exptdata: data for expt as dict
        :return: expt or None
        """
        expt = None
        if subject is not None:
            mandata['experiments'] = xsdtype
            mandata['ID']= exptid
            logging.debug(mandata)
            if xsdtype + '/date' in mandata:
                vdate = mandata[xsdtype + '/date']
                if "-" in vdate:
                    expt_creation = datetime.datetime.strptime(mandata[xsdtype + '/date'], "%Y-%m-%d")
                else:
                    expt_creation = datetime.datetime.strptime(mandata[xsdtype + '/date'],"%Y.%m.%d %H:%M:%S")
                del mandata[xsdtype + '/date']
            else:
                expt_creation = datetime.datetime.now()
            expt_creation_date = expt_creation.strftime("%Y%m%d")
            expt_creation_time = expt_creation.strftime("%H:%M:%S")
            #create with mandatory data
            expt = subject.experiment(exptid).create(**mandata)
            if not expt.exists():
                msg = 'Cannot create expt: %s' % exptid
                raise ValueError(msg)
            # Add attributes as other fields
            expt.attrs.set('xnat:experimentData/date', expt_creation_date)
            expt.attrs.set('xnat:experimentData/time', expt_creation_time)
            expt.attrs.mset(exptdata)

        return expt

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

    def updateExptDate(self,subject,exptid,exptdate, dsitype):
        """
        Update existing experiment date
        :param subject: Subject obj
        :param exptid:
        :param exptdate:
        :param dsitype:
        :return:
        """
        #project = self.get_project(projectcode)
        expt = subject.experiment(exptid)
        if expt.exists():
            #format date
            if not isinstance(exptdate, datetime.datetime):
                exptdate = datetime.datetime.strptime(exptdate, "%Y-%m-%d %H:%M:%S")
            edate = expt.attrs.get('xnat:experimentData/date')
            if edate != exptdate.strftime("%Y-%m-%d"):
                expt.attrs.set('xnat:experimentData/date', exptdate.strftime("%Y%m%d"))
                expt.attrs.set('xnat:experimentData/time', exptdate.strftime("%H:%M:%S"))
                print "Updated experiment date: ", expt.id()
                return expt
            else:
                return None
        else:
            return None

    def changeExptLabel(self,projectcode, oldlabel, newlabel):
        """
        Change label for an experiment - currently OPEX
        NOTE: Need to Load mandatory fields and subject ID
        Alternatively works on spreadsheet upload with these fields selected
        :param projectcode:
        :param oldlabel:
        :param newlabel:
        :return:
        """
        project = self.get_project(projectcode)
        expt = project.experiment(oldlabel)
        if expt.exists():
            xsd = expt.datatype()
            mandata = {
                xsd + '/label': newlabel,
                xsd + '/interval': expt.attrs.get(xsd + '/interval'),
                xsd + '/sample_quality': expt.attrs.get(xsd + '/sample_quality'),
                xsd + '/data_valid': expt.attrs.get(xsd + '/data_valid'),
                'subject_ID':expt.attrs.get('subject_ID')
            }
            print "Old:", expt.label()
            expt.attrs.mset(mandata)
            print "New:", expt.label()
        else:
            print("No expts found with label=", oldlabel)

    def getSubjectsDataframe(self,projectcode, dsitype=None,columns=None, criteria=None):
        """
        Gets subject label, id as dataframe
        :param projectcode:
        :return:
        """
        if columns is None:
            columns = ['xnat:subjectData/SUBJECT_LABEL', 'xnat:subjectData/SUBJECT_ID','xnat:subjectData/SUB_GROUP','xnat:subjectData/GENDER_TEXT', 'xnat:subjectData/DOB']
        if criteria is None:
            criteria = [('xnat:subjectData/SUBJECT_ID', 'LIKE', '*'), 'AND']
        if dsitype is None:
            dsitype = 'xnat:subjectData'
        subj = self.conn.select(dsitype, columns).where(criteria)
        #Convert to dataframe
        if len(subj) > 0:
            df_subjects = pd.DataFrame(list(subj))
            if 'xnat_subjectdata_subject_id' in df_subjects.columns:
                df_subjects.rename(columns={'xnat_subjectdata_subject_id': 'subject_id'},inplace=True)
            #print(df_subjects.head())
        else:
            df_subjects = None
        return df_subjects


    def upload_MRIscans(self, projectcode, scandir, opexid=False):
        """
        Upload MRI scans from scandir to project
        :param projectcode: XNAT ID for project eg QBICC
        :param scandir: full path name of dir containing subdirs with data
        eg /ibscratch/irc5scans/data
        data should be organized by DICOM series as: data/subject_label/scans/series_number/*.dcm (or *.IMA)
        :return: number of sessions loaded
        """
        import re
        project = self.get_project(projectcode)
        #owners = project.owners()
        #proj_pi = self.get_projectPI(projectcode)
        ctr = 0
        default_scantype = 'MR Image Storage'
        #load
        scanfiles = [f for f in listdir(scandir) if os.path.isdir(join(scandir, f))]
        if scanfiles:
            dirpath = os.path.dirname(scandir)
            #opex
            visitid = scandir.rsplit('_', 1)
            if len(visitid) > 1:
                m = re.match('(\d){1,2}[mM]?$', visitid[1])
                visitid = int(m.group(1))
            else:
                visitid = 1
            donepath = join(dirpath, 'done')
            if not os.path.isdir(donepath):
                try:
                    os.mkdir(donepath)
                except:
                    raise OSError

        for slabel in scanfiles:
            if opexid and len(slabel) > 6:
                # try to extract slabel eg 1006JJ06
                sid = self.get_subjectid_bylabel(projectcode, slabel[0:6])
            else:
                sid = self.get_subjectid_bylabel(projectcode, slabel)
            if sid is None:

                logging.warning("Subject doesn't exist - skipping %s", slabel)
                continue
            s = project.subject(sid)

            if s.exists():
                ctr = ctr + 1
                # Set experiment
                elabel = 'MR_%s_%d' % (s.label(), visitid)
                elabel = self.checkUniqueLabel(s, elabel)  # eid = self.find_next_experimentID(projectcode, prefix,True)
                message = "Uploading scans for %s: %s with expt=%s" % (s.id(), s.label(), elabel)
                logging.info(message)
                print(message)
                expt = s.experiment(elabel)
                expt.create()  # experiments='xnat:mrSessionData')
                expt.attrs.set('xnat:mrSessionData/visit_id', str(visitid)) #could change to 0m?
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
                    scan_pi = self.getPI(scan_files[0])
                    print('Scan ID:', scan_id, 'Scan type=', scan_type, 'Scan info=',scan_pi)
                    # (scan_date, scan_time) = self.getSeriesDatestamp(scan_files[0])
                    scan_ctr += 1
                    scan = expt.scan(str(scan_id))
                    # Refer to scan types in DICOMSOP.csv
                    if scan_type == 'MR Image Storage' or '1.2.840.10008.5.1.4.1.1.4' in scan_type:
                        scan.create(scans='xnat:mrScanData')
                        logging.info("Scan created[%s]:  MR Image Storage [%s] - %s", scan_id, scan_type, scan_pi)
                    elif scan_type == 'Secondary Capture Image Storage' or '1.2.840.10008.5.1.4.1.1.7' in scan_type:
                        scan.create(scans='xnat:scScanData')
                        logging.info("Scan created[%s]:  Secondary Capture Image Storage [%s] - %s", scan_id, scan_type, scan_pi)
                    else:
                        modality = self.getModality(scan_files[0])
                        if modality is not None and modality == 'MR':
                            scan.create(scans='xnat:otherDicomScanData')
                            logging.info("Scan created[%s]:  Other DICOM [%s] - %s", scan_id, scan_type, scan_pi)

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
            type = dcm.SOPClassUID #see references at http://dicomlookup.com/dicom-sop.asp

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

    def delete_subjects_all(self,projectcode):
        """
        Removes all subjects from a project
        """
        project = self.get_project(projectcode)
        subj = self.get_subjects(projectcode)
        for s in subj:
            sid = s.id()
            print "Deleting:", s.label()," ID=",sid
            project.subject(sid).delete()
            if project.subject(sid).exists():
                print "ERROR: Couldn't delete ID=", sid

    def delete_experiments(self, projectcode, datatype, fields):
        """
        Removes experiments with corresponding field-values
        """
        #expts = self.conn.inspect.experiment_values(datatype, projectcode)
        project = self.get_project(projectcode)
        row = datatype
        for field in fields:
            fieldref = datatype + '/' + field
            columns = [datatype + '/SUBJECT_ID', datatype + '/ID', fieldref]
            criteria = [(fieldref, 'LIKE', fields[field]),
                    'AND'
                    ]
            self.conn.manage.search.save('deleting', row, columns, criteria) #save search
            elist = self.conn.manage.search.get('deleting') #run search
            print datatype, " Expts to delete:", len(elist)
            for e in elist:
                print e
                expt = project.experiment(e['expt_id'])
                expt.delete()
                if (project.experiment(e['expt_id']).exists()):
                    print "ERROR: Couldn't delete Expt ID=", e['expt_id']
                else:
                    print "DELETED:", e['expt_id']
            xnat.conn.manage.search.delete('deleting') #remove saved search


############################################################################################
if __name__ == "__main__":
    # get current user's login details (linux) or local file (windows)
    home = expanduser("~")
    configfile = join(home, '.xnat.cfg')
    parser = argparse.ArgumentParser(prog='XnatConnector',
        description='''\
        XnatConnector: Script for managing data in QBI XNAT db
         ''')
    parser.add_argument('database', help='select database to connect to [qbixnat|irc5xnat]')
    parser.add_argument('projectcode', help='select project by code eg QBICC')
    parser.add_argument('--p', action='store_true', help='list projects')
    parser.add_argument('--s', action='store_true', help='list subjects')
    parser.add_argument('--x', action='store_true', help='delete subjects')
    parser.add_argument('--m', action='store_true', help='delete experiments (opex,aborted)')
    parser.add_argument('--c1', action='store', help='change expt label from')
    parser.add_argument('--c2', action='store', help='change expt label to')
    parser.add_argument('--counts', action='store_true', help='Get experiment counts for subjects')
    parser.add_argument('--config', action='store', help='database configuration file (overrides ~/.xnat.cfg)')
    #Tests
    #args = parser.parse_args(['xnat-dev', 'TEST_PJ00', '--p']) #Preset
    args = parser.parse_args()
    print args
    xnat = XnatConnector(configfile, args.database)
    print "Connecting to URL=", xnat.url
    xnat.connect()
    if (xnat.conn):
        print "...Connected"
        try:
            projectcode = args.projectcode  # "QBICC"
            if (args.x is not None and args.x):
                xnat.delete_subjects_all(projectcode)

            if (args.s is not None and args.s):
                xnat.list_subjects_all(projectcode)

            if (args.p is not None and args.p):
                projlist = xnat.list_projects()
                for p in projlist:
                    print "Project: ", p.id()

            if (args.c1 is not None and args.c2 is not None):
                xnat.changeExptLabel(projectcode, args.c1, args.c2)


            if (args.m is not None and args.m):
                etypes = sorted(xnat.conn.inspect.datatypes())
                print(etypes)
                for dtype in ['opex:bloodCobasData']:
                    xnat.delete_experiments(projectcode,dtype,{'sample_quality':'UNKNOWN'}) # 'status': 'SYSTEM_ERROR'
                # for dtype in ['opex:cantabDMS','opex:cantabERT','opex:cantabMOT','opex:cantabPAL','opex:cantabSWM']:
                #     xnat.delete_experiments(projectcode,dtype,{'status': 'COMPLETED'}) # 'status': 'SYSTEM_ERROR'
        except ValueError as e:
            print "Error:", e

        finally:
            xnat.conn.disconnect()
            print("FINISHED")

    else:
        print "Failed to connect"