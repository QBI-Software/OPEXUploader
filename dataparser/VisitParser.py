# -*- coding: utf-8 -*-
"""
Utility script: VisitParser
Reads an excel or csv file with data and extracts per subject
run from console/terminal with (example):
>python VisitParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
from os import R_OK, access
from os.path import join
import pandas as pd
from datetime import datetime
from numpy import isnan
import logging

from dataparser.DataParser import DataParser

VERBOSE = 0
class VisitParser(DataParser):

    def __init__(self, *args):
        DataParser.__init__(self, *args)
        self.opex = pd.read_csv(join('resources', 'opex.csv'))

    def getSubjectData(self,sd):
        """
        Extract subject data from input data
        :param sd:
        :return:
        """
        skwargs = {}
        if self.subjects is not None:
            dob = self.formatDobNumber(self.subjects[sd]['DOB'].iloc[0])
            gender = str(self.subjects[sd]['Sex'].iloc[0]).lower()
            skwargs = {'dob': dob}
            if gender in ['F', 'M']:
                skwargs['gender'] = gender

        return skwargs

    def futureDate(self, d):
        """
        Check if date is in future
        :param d: date as datetime
        :return: true if is in future
        """
        thisdate = datetime.today()
        return d > thisdate

    def updateGenders(self, projectcode=None, xnat=None):
        """
        UPdate gender info
        :param projectcode:
        :param xnat:
        :return:
        """
        xnatgenders={'F':'female', 'M': 'male'}
        for i, sd in self.data.iterrows():
            subject_id = sd['ID'].replace(" ", "")
            g = sd['Sex']
            if g == 'U':
                continue
            gender = xnatgenders[g]            # if subject in database, else skip

            if xnat is not None:
                project = xnat.get_project(projectcode)
                s = project.subject(subject_id)
                if not s.exists():
                    continue
                xgender = s.attrs.get('gender')
                if gender != xgender:
                    s.attrs.mset({'gender': gender})
                    msg = 'Subject gender updated: %s to %s' % (subject_id, gender)
                    print msg
                    logging.info(msg)
            else:
                msg = 'Subject gender to update: %s to %s' % (subject_id, gender)
                print msg

    def processData(self, projectcode=None, xnat=None):
        """
        Process data from file - upload to XNAT per expt
        :param projectcode: XNAT project code (eg P1)
        :param xnat: XnatConnector obj
        :return: nothing
        """
        intvals = [str(i) for i in range(0, 13)]
        for i, sd in self.data.iterrows():
            subject_id = sd['ID'].replace(" ", "")
            # if subject in database, else skip
            if xnat is not None:
                project = xnat.get_project(projectcode)
                s = project.subject(subject_id)
                if not s.exists():
                    continue
            # get each experiment and check date matches - these are upload dates by default
            for expt in ['DEXA', 'COBAS', 'ELISAS', 'MULTIPLEX', 'MRI ASHS', 'MRI FS', 'FMRI']:
                prefix = self.opex['prefix'][self.opex['Expt'] == expt].values[0]
                xtype = self.opex['xsitype'][self.opex['Expt'] == expt].values[0]
                if xnat is not None and s is not None:
                    xexpts = s.experiments(prefix + '_*')
                    if len(xexpts.fetchall()) <=0:
                        if expt =='FMRI': #IDS are OPEXNAT*
                            labels = [e.label() for e in s.experiments('OPEXNAT*') if e.label().startswith(expt)]
                            if len(labels) <= 0:
                                continue
                        else:
                            continue

                for intval in intvals:
                    if expt in ['COBAS', 'ELISAS', 'MULTIPLEX']:
                        subexpts = ["FASTED", "PREPOST"]
                        for se in subexpts:
                            eint = "BLOOD_" + se + "_" + intval
                            if eint not in sd:
                                continue
                            d = sd[eint]
                            if se == "PREPOST":
                                for sexpt in ['PRE','POST']:
                                    exptid = "%s_%s_%sm_%s_%d" % (prefix, subject_id, intval, sexpt.lower(), 1)
                                    if isinstance(d, datetime) and not isnan(d.day) and not self.futureDate(d):
                                        msg = "Subject: %s | Type: %s | ID: %s | Date: %s | Exptid: %s" % (subject_id, xtype, eint, d, exptid)
                                        print msg
                                    if xnat is not None and s is not None:
                                        #Get correct ID - last digit may vary
                                        e = s.experiment(exptid)
                                        if not e.exists():
                                            # check for similar but difnt counter for bloods
                                            expts = s.experiments(exptid[0:-2] + '*')
                                            xnatexpt = expts.fetchone()
                                            if xnatexpt is None or not xnatexpt.exists():
                                                print "Expt not found: ", exptid
                                                continue
                                            else:
                                                exptid = xnatexpt.id()
                                        xnatexpt = xnat.updateExptDate(s,exptid, d, xtype)
                                        if xnatexpt is not None:
                                            #remove or update comment
                                            xnatexpt.attrs.set(xtype + '/comments', 'Date updated')
                                            msg = '%s date updated %s' % (xnatexpt.id(),d)
                                            logging.info(msg)
                            else:
                                exptid = "%s_%s_%sm_%s_%d" % (prefix, subject_id, intval, se.lower(), 1)
                                if isinstance(d, datetime) and not isnan(d.day) and not self.futureDate(d):
                                    msg = "Subject: %s | Type: %s | ID: %s | Date: %s | Exptid: %s" % (
                                    subject_id, xtype, eint, d, exptid)
                                    print msg
                                if xnat is not None and s is not None:
                                    e = s.experiment(exptid)
                                    if not e.exists():
                                        # check for similar but difnt counter for bloods
                                        expts = s.experiments(exptid[0:-2] + '*')
                                        xnatexpt = expts.fetchone()
                                        if xnatexpt is None or not xnatexpt.exists():
                                            print "Expt not found: ", exptid
                                            continue
                                        else:
                                            exptid = xnatexpt.id()
                                    xnatexpt = xnat.updateExptDate(s, exptid, d, xtype)
                                    if xnatexpt is not None:
                                        # remove or update comment
                                        xnatexpt.attrs.set(xtype + '/comments', 'Date updated')
                                        msg = '%s date updated %s' % (xnatexpt.id(), d)
                                        logging.info(msg)
                    else:
                        if expt in ['MRI ASHS', 'MRI FS', 'FMRI']:
                            eint = "MRI_" + intval
                        else:
                            eint = expt + "_" + intval
                        if eint not in sd:
                            continue
                        d = sd[eint]
                        exptid = "%s_%s_%s" % (prefix, subject_id, intval)
                        if isinstance(d, datetime) and not isnan(d.day) and not self.futureDate(d):
                            msg = "Subject: %s | Type: %s | ID: %s | Date: %s | Exptid: %s" % (
                            subject_id, xtype, eint, d, exptid)
                            print msg
                            if xnat is not None and s is not None:
                                xnatexpt = xnat.updateExptDate(s,exptid, d, xtype)
                                if xnatexpt is not None:
                                    # remove or update comment
                                    comments = xnatexpt.attrs.get(xtype + '/comments')
                                    if len(comments) > 0:
                                        if not 'Date updated' in comments:
                                            xnatexpt.attrs.set(xtype + '/comments', comments + '; Date updated')
                                        #replace if multiple
                                        elif comments.startswith('Date updated'):
                                            xnatexpt.attrs.set(xtype + '/comments', 'Date updated')
                                    else:
                                        xnatexpt.attrs.set(xtype + '/comments', 'Date updated')
                                    msg = '%s date updated %s' % (xnatexpt.id(), d)
                                    logging.info(msg)


########################################################################

if __name__ == "__main__":
    import os

    parser = argparse.ArgumentParser(prog=os.sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')

    parser.add_argument('--file', action='store', help='File with data', default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\visit\\Visits.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract', default=1)
    args = parser.parse_args()

    inputfile = args.file
    print("Input:", inputfile)
    try:
        print("Loading",inputfile)
        dp = VisitParser(inputfile,args.sheet,1)
        #dp.processData()
        dp.updateGenders()

    except Exception as e:
        print e

