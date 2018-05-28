# -*- coding: utf-8 -*-
"""
Utility script: BloodParser
Reads an excel or csv file with data and extracts per subject
run from console/terminal with (example):
>python BloodParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
import re
from datetime import datetime
from os import R_OK, access
from os.path import join

import pandas

from opexuploader.dataparser.abstract.DataParser import DataParser

DEBUG = 0
class BloodParser(DataParser):

    def __init__(self, *args, **kwargs):
        DataParser.__init__(self, *args)
        if self.data is None:
            raise ValueError('BloodParser: Data not loaded')
        self.type=''
        if 'type' in kwargs:
            self.type = kwargs.get('type')
            self.fields = self.dbi.getFields(self.type)
            self.info = self.dbi.getInfo(self.type)
            #self.fields = self.getFieldsFromFile(self.type)
        elif self.etype is not None:
            self.type = self.etype

        # Multiplex has different headers vs Cobas
        if self.type == 'MULTIPLEX':
            print('Headers for ', self.type)
            colnames = {'Date': 'A_Date', 'Participant ID ': 'Participant ID', 'Timepoint': 'Sample ID','IGFBP-7':'IGFBP7'}
            self.data = self.data.rename(index=str, columns=colnames)
            self.data.insert(0, 'R_No.', range(len(self.data)))
        elif self.type == 'ELISAS':
            colnames = ['BetaHydroxy','Sample ID','A_Date','R_No.','Participant ID','Timepoint']
            try:
                df = self.data[colnames]
                self.data = df
            except Exception as e:
                raise ValueError(e)
            #self.data = self.data.rename(index=str, columns=colnames)
        elif self.type == 'COBAS':
            # Rename columns to field names
            if self.fields[0] not in self.data.columns:
                colnames = {}
                v=1
                for i in range(len(self.fields)):
                    colnames['Value.' + str(v)] = self.fields[i]
                    v = v + 2

                df = self.data.rename(index=str, columns=colnames)
                print("Renamed columns: ", colnames)
                self.data = df
        # Remove NaT rows
        i = self.data.query('A_Date =="NaT"')
        if not i.empty:
            self.data.drop(i.index[0], inplace=True)
            print('NaT row dropped')
        # Organize data into subjects
        subjectfield ='Participant ID'
        if subjectfield not in self.data.columns:
            raise ValueError('Subject ID field not present: ', subjectfield)
        self.data[subjectfield] = self.data[subjectfield].str.replace(" ","")
        self.sortSubjects(subjectfield)
        if self.subjects is not None:
            print('BloodParser: subjects loaded successfully')

    def getInterval(self,rowval):
        print('getinterval',rowval)

    def getFieldsFromFile(self, type):
        """
        Get list of fields for subtype
        :param self:
        :return:
        """
        fields=[]
        try:
            fieldsfile = join(self.resource_dir, 'blood_fields.csv')
            df = pandas.read_csv(fieldsfile, header=0)
            fields = df[self.type]
            fields.dropna(inplace=True)
        except Exception as e:
            raise e
        return fields

    def getPrepostOptions(self,i):
        options = ['fasted', 'pre', 'post']
        return options[i]

    def parseSampleID(self,sampleid):
        """
        Splits sample id
        :param sampleid: 0-0-S-a gives interval-prepost-S-a
        :return: interval, prepost string
        """
        parts = sampleid.split("-")
        if len(parts) == 4:
            interval = int(parts[0])
            prepost = self.getPrepostOptions(int(parts[1]))
        else:
            interval = -1
            prepost = ""
        return (interval, prepost)

    def parseTimepoint(self,timepoint):
        m = re.search('^(\d{1,2})m\s(\w+)', timepoint)
        interval = m.group(1)
        prepost = m.group(2)
        return (interval, prepost)

    def getSampleid(self, sd, row):
        """
        Generate a unique id for data sample
        :param row:
        :return:
        """
        if 'Timepoint' in row:
            (interval, prepost) = self.parseTimepoint(row['Timepoint'])
            m_sid = re.search('(\d{1,2})', row['R_No.'])
            id = "%s_%dm_%s_%s" % (sd, int(interval), prepost, int(m_sid.group(1)))
            # print('Timepoint: id=', id)
        elif 'Sample ID' in row:
            parts = row['Sample ID'].split("-")
            id = "%s_%dm_%s_%s" % (sd, int(parts[0]), self.getPrepostOptions(int(parts[1])), int(row['R_No.']))
            # print('SampleID: id=', id)
        else:
            raise ValueError("Sample ID column missing")
        return id

    def formatADate(self, orig):
        """
        Formats date from input as dd/mm/yyyy hh:mm:ss
        :param orig:
        :return:
        """
        if isinstance(orig, pandas.Timestamp):
            dt = orig
        elif "/" in orig:
            dt = datetime.strptime(orig, "%d/%m/%Y %H:%M:%S")
        elif "-" in orig:
            dt = datetime.strptime(orig, "%Y-%m-%d %H:%M:%S")
        else:
            dt = orig
        return dt.strftime("%Y.%m.%d %H:%M:%S")

    def mapData(self, row, i, xsd=None):
        """
        Maps required fields from input rows
        :param row:
        :return:
        """
        if self.type=='ELISAS':
            (interval,prepost) = self.parseTimepoint(row['Timepoint'])
            sample_id = row['Sample ID']
            sample_num = str(row['R_No.'])
        else:
            (interval, prepost) = self.parseSampleID(row['Sample ID'])
            sample_id = row['Sample ID']
            sample_num = str(row['R_No.'])

        if xsd is None:
            xsd = self.getxsd() #[self.type]
        mandata = {
            xsd + '/interval': str(interval),
            xsd + '/sample_id': sample_id,  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/date' : self.formatADate(row['A_Date']),
            xsd + '/comments' : 'Date analysed',
            xsd + '/prepost': prepost,
            xsd + '/sample_num' : sample_num

        }
        #Different fields for different bloods
        data = {}
        for ctab in self.fields:
            if ctab in row:
                if DEBUG:
                    print(ctab, ' = ', row[ctab])
                data[xsd + '/' + ctab] = str(row[ctab])

        return (mandata,data)




########################################################################

if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads files in a directory and extracts data ready to load to XNAT database

             ''')

    parser.add_argument('--filedir', action='store', help='Directory containing files', default="Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata\\blood\\ELISAS")
    parser.add_argument('--sheet', action='store', help='Sheet name to extract', default="0")
    parser.add_argument('--type', action='store', help='Type of blood sample', default="ELISAS")
    args = parser.parse_args()

    inputdir = args.filedir
    sheet = int(args.sheet)
    skip = 1
    header=None
    etype = args.type
    if args.type =='MULTIPLEX':
        skip =0
    elif args.type=='ELISAS':
        skip=34
    print("Input:", inputdir)
    if access(inputdir, R_OK):
        seriespattern = '*.xlsx'

        try:
            files = glob.glob(join(inputdir, seriespattern))
            print("Files:", len(files))
            for f2 in files:
                print("\n****Loading",f2)
                dp = BloodParser(f2,sheet,skip, header,etype)

                for sd in dp.subjects:
                    print('ID:', sd)
                    for i, row in dp.subjects[sd].iterrows():
                        dob = dp.formatADate(str(dp.subjects[sd]['A_Date'][i]))
                        uid = dp.getPrefix() + "_" + dp.getSampleid(sd,row)
                        print(i, 'Visit:', uid, 'Date', dob)
                        (d1,d2) = dp.mapData(row,i)
                        print(d1)
                        print(d2)



        except ValueError as e:
            print(e)

    else:
        print("Cannot access directory: ", inputdir)
