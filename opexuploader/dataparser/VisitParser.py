from __future__ import print_function
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
from datetime import datetime
import logging

from opexuploader.dataparser.abstract.DataParser import DataParser, stripspaces

VERBOSE = 0
class VisitParser(DataParser):

    def __init__(self, *args):
        DataParser.__init__(self, *args)
        #self.opex = pd.read_csv(join(self.resource_dir, 'opex.csv'))
        self.expts = dict()

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

    def validDate(self, d):
        """
        Check if date is valid and not in future
        :param d: date as datetime
        :return: true if is in future
        """
        rtn = isinstance(d, datetime)
        if rtn:
            checks ="%s" % d
            if checks != 'NaT':
                thisdate = datetime.today()
                rtn= d <= thisdate
            else:
                rtn = False
        return rtn


    def updateGenders(self, projectcode=None, xnat=None):
        """
        UPdate gender info if provided
        :param projectcode:
        :param xnat:
        :return:
        """
        # Check data has required fields
        if not 'ID' in self.data.columns or not 'Sex' in self.data.columns:
            print('Cannot run update genders as data is not present')
            return 0

        xnatgenders={'F':'female', 'M': 'male'}
        for i, sd in self.data.iterrows():
            subject_id = self.getValidSid(sd['ID'])
            if not subject_id:
                continue
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
                    print(msg)
                    logging.info(msg)
            else:
                msg = 'Subject gender to update: %s to %s' % (subject_id, gender)
                print(msg)

    def getValidSid(self, sid):
        if isinstance(sid,int):
            checksid = False
        else:
            checksid = sid.replace(" ", "")
            if len(str(checksid)) > 6:
                checksid = checksid[0:6]
            checksid = self._DataParser__checkSID(checksid)

        return checksid

    def processData(self):
        """
        Process data file and compile exptids with dates
        :return:
        """
        intvals = [str(i) for i in range(0, 13)]
        # get each experiment and check date matches - these are upload dates by default as dates were not provided with the data
        #  ['DEXA', 'COBAS', 'ELISAS', 'MULTIPLEX', 'MRI ASHS', 'MRI FS', 'FMRI', 'DASS']
        dateless = self.dbi.getDatelessExpts() #opex['Expt'][self.opex['date_provided'] == 'n'].values
        print("Dateless expts: ",dateless)
        for i, sd in self.data.iterrows():
            subject_id = self.getValidSid(sd['ID'])
            if not subject_id:
                continue
            for expt in dateless:
                info = self.dbi.getInfo(expt)
                prefix = info['prefix']
                xtype = info['xsitype']
                for intval in intvals:
                    if xtype.startswith('opex:blood'):
                        subexpts = ["FASTED", "PREPOST"]
                        for se in subexpts:
                            eint = "BLOOD_" + se + "_" + intval
                            if eint not in sd:
                                continue
                            # Get date
                            d = sd[eint]
                            if self.validDate(d):
                                if se == "PREPOST":
                                    for sexpt in ['PRE', 'POST']:
                                        exptid = "%s_%s_%sm_%s_%d" % (prefix, subject_id, intval, sexpt.lower(), 1)
                                        #save data
                                        self.expts[exptid] = d
                                else:
                                    exptid = "%s_%s_%sm_%s_%d" % (prefix, subject_id, intval, se.lower(), 1)
                                    self.expts[exptid] = d
                    else:
                        exptid = "%s_%s_%s" % (prefix, subject_id, intval)
                        # Get Column from Visits
                        if expt in ['MRI ASHS', 'MRI FS', 'FMRI']:
                            eint = "MRI_" + intval
                        # assessment B
                        elif expt in ['DEXA', 'DASS', 'GODIN', 'PSQI','Insomnia']:
                            eint = "DEXA_" + intval
                            if expt != 'DEXA':
                                exptid += 'M'  # M added to some IDs
                        # assessment A
                        elif expt in ['CANTAB', 'ACER']:
                            eint = "CANTAB_" + intval
                        else:
                            eint ='na'
                        if eint not in sd:
                            continue
                        d = sd[eint]
                        if self.validDate(d):
                            self.expts[exptid] = d

        return self.expts

    def uploadDates(self, projectcode=None, xnat=None):
        """
        Update dates in XNAT - if different
        :param projectcode:
        :param xnat:
        :return:
        """
        print("**Uploading dates to XNAT**")
        missing =[]
        matches=[]
        if xnat is not None:
            project = xnat.get_project(projectcode)
        else:
            raise IOError("XNAT not connected")

        for eid in self.expts.keys():
            d = self.expts.get(eid)
            prefix = eid.split('_')[0]
            subject_id = eid.split('_')[1]
            xtype = self.dbi.getXsitypeFromPrefix(prefix)
            s = project.subject(subject_id)
            if not s.exists():
                continue
            e = s.experiment(eid)
            if xtype.startswith('opex:blood'):
                expts = s.experiments(eid[0:-2] + '*')
                e = expts.fetchone()
            # elif xtype == 'opex:fmri':
            #     expts = [e.id() for e in s.experiments('OPEXNAT*') if e.label() == eid]
            #     if len(expts) > 0:
            #         eid = expts[0]
            #         e = s.experiment(eid)
            #     else:
            #         continue
            if e is not None and e.exists():
                exptid = e.id()
                msg = 'Found expt: %s %s : %s [%s]' % (subject_id,xtype, exptid,eid)
                #print(msg)
                logging.debug(msg)
                xnatexpt = xnat.updateExptDate(s, exptid, d, xtype)
                if xnatexpt is not None: #not updated if not different
                    # remove or update comment
                    comments = xnatexpt.attrs.get(xtype + '/comments')
                    if len(comments) > 0:
                        if comments != 'Date analysed not collected' and not 'Date updated' in comments:
                            comments = comments + '; Date updated'
                    else:
                        comments = 'Date updated'
                    xnatexpt.attrs.set(xtype + '/comments', comments)
                    matches.append(xnatexpt.id())
                    msg = 'UPDATED %s %s date - %s' % (subject_id, xnatexpt.id(), d)
                    print(msg)
                    logging.info(msg)
            else:
                msg = "Expt not found: %s" % eid
                logging.debug(msg)
                #print msg


        print("Total updates: ", len(matches))
        return (missing,matches)


########################################################################

if __name__ == "__main__":
    import os

    parser = argparse.ArgumentParser(prog=os.sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')

    parser.add_argument('--file', action='store', help='File with data', default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\visit\\Visits.xlsx")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract', default=0)
    args = parser.parse_args()

    inputfile = args.file
    print("Input:", inputfile)
    try:
        print("Loading",inputfile)
        dp = VisitParser(inputfile,args.sheet,1)
        #dp.updateGenders()
        dp.processData()
        # print(output
        print("**Processed dates**")
        for eid in dp.expts.keys():
            print(eid, ": ", dp.expts.get(eid))

    except Exception as e:
        print(e)

