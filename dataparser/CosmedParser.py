# -*- coding: utf-8 -*-
"""
Utility script: CosmedParser
COSMED data requires further calculation and filtering before compiling for upload
1. Individual data files are stored in directory with filename as: subjectid_xMonth[A|B|C|D]_30sec_yyyymmdd.xlsx
 - ignore files 0MonthA
 - group files 0MonthB, 3MonthC, 6MonthD
 - date of expt (full date and time in spreadsheet)
2. Load Fields listed in cosmed_fields.xlsx
    - cosmed tab: read SubjectID, date and time as per row/column from "Data" tab
    - cosmed_xnat: map XnatField to Parameter
    - cosmed_fields: shows how data is collected - not read directly
    - cosmed_data: header fields for parsing data
3. Load data file with skip=0 sheetname='Data'
    - SubjectID = cell(1,1)
    - date = cell(0,4) - format d/m/yyyy
    - time = cell(1,4) - format hh:mm:ss AM/PM
    - subset with 'cosmed_data'[0] as columns -> phasedata
        + Find phase=EXERCISE - last time point - extract data fields as per cosmed_fields
        + subset EXERCISE data at 3min intervals
        + subset RECOVERY data at 1min interval
4. Load data file with skip=0 sheetname='Results'
    - extract line 5 for headers
    - read params and Max for xnat
5. Generate phase data from subsets
    - write to new tab with Results data 'ScriptResults'
6. Load another data file: VO2data_VEVCO2_20171009.xlsx (?date variable)
    - read 'Efficiency' params - line by line per subject (post-update)

run from console/terminal with (example):
>python CosmedParser.py --filedir "data" --sheet "Sheetname_to_extract"

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

import argparse
import glob
import logging
import re
from datetime import datetime, time
from os import R_OK, access, mkdir
from os.path import join, basename, split, isdir, dirname, abspath

import numpy as np
import pandas as pd
from openpyxl import load_workbook

from dataparser.DataParser import stripspaces

VERBOSE = 1


# Not using DataParser as too complex
class CosmedParser():
    def __init__(self, inputdir, inputsubdir, datafile, testonly=False):
        self.inputdir = inputdir
        self.testonly = testonly
        # Load fields
        fieldsfile = join(self.getResourceDir(), "cosmed_fields.xlsx")
        self.subjectdataloc = pd.read_excel(fieldsfile, header=0, sheetname='cosmed')
        self.fields = pd.read_excel(fieldsfile, header=0, sheetname='cosmed_xnat')
        self.datafields = pd.read_excel(fieldsfile, header=0, sheetname='cosmed_data')

        # Get list of subjects - parse individual files
        self.subjects = dict()
        self.files = glob.glob(join(inputsubdir, "*.xlsx"))
        # create an output dir for processed files
        pdir = join(inputsubdir, 'processed')
        if not isdir(pdir):
            mkdir(pdir)

        # Load efficiency data from single file
        self.effdata_cols = {'0': [5, 8], '3': [9, 12], '6': [13, 16], '9': [17, 20], '12': [21, 24]}
        self.effdata = self.__loadEfficiencydata(datafile)
        # Load data from files
        self.loaded = self.__loadData()

    def getResourceDir(self):
        resource_dir = glob.glob(join(dirname(__file__), "resources"))
        middir = ".."
        ctr = 1
        while len(resource_dir) <= 0 and ctr < 5:
            resource_dir = glob.glob(join(dirname(__file__), middir, "resources"))
            middir = join(middir, "..")
            ctr += 1
        return abspath(resource_dir[0])

    def __loadEfficiencydata(self, datafile):
        # Load efficiency data from single file
        effdata = pd.read_excel(datafile, sheetname=0, header=1)
        effdata.drop(effdata.index[0], inplace=True)
        effdata['SubjectID'] = effdata.apply(lambda x: stripspaces(x, 'ID'), axis=1)
        logging.debug("Loaded Efficiency: %d", len(effdata))
        return effdata

    def __loadData(self):
        rtn = False
        # Load data from files
        cols = ['SubjectID', 'interval', 'date', 'time', 'filename'] + self.fields['Parameter'].tolist()
        self.data = {i: [] for i in cols}
        f = None
        try:
            for f in self.files:
                filename = basename(f)
                #exclude certain files
                if "MonthA" in filename or "_10s" in filename or filename.startswith('~') or filename.startswith('VO2'):
                    continue
                fdata = self.parseFilename(filename)
                if fdata is None:
                    msg = 'Skipping file: %s' % filename
                    logging.warning(msg)
                    continue
                else:
                    msg = "File: %s" % filename
                    logging.info(msg)

                df_file_data = pd.read_excel(f, header=0, sheetname='Data')
                if 'Dyspnea' in df_file_data.columns:
                    # Replace LEVEL with int
                    df_file_data['Dyspnea'] = df_file_data['Dyspnea'].apply(lambda r: self.extractLevel(r))
                else:
                    msg = 'Dyspnea column missing in %s' % filename
                    logging.error(msg)
                    print(msg)
                    df_file_data.insert(len(df_file_data.columns),'Dyspnea','')
                df_data_ex = df_file_data[df_file_data['Phase'] == 'EXERCISE']
                df_data_rec = df_file_data[df_file_data['Phase'] == 'RECOVERY']
                df_file_results = pd.read_excel(f, header=0, sheetname='Results', skiprows=4)
                if (df_file_data.iloc[0, 3] == 'Test Time'):
                    ftime = df_file_data.iloc[0, 4]  # format with date
                else:
                    ftime = ''
                fdata.append(ftime)
                self.data['time'].append(ftime)
                protocoldata = self.parseProtocol(df_file_results, df_data_ex, self.fields['Parameter'].tolist()[0:4])
                metabolicdata = self.parseMetabolic(df_file_results, self.fields['Parameter'].tolist()[4:8])
                cardiodata = self.parseCardio(df_data_ex, self.fields['Parameter'].tolist()[8:14])
                effdata = self.parseEfficiency(self.effdata, fdata[0], self.effdata_cols[fdata[1]])
                recoverydata = self.calcRecovery(df_data_ex, df_data_rec)
                row = fdata + protocoldata + metabolicdata + cardiodata + effdata + recoverydata
                print("Row: ", row)

                if not self.testonly:
                    # Generate phase data as separate tab
                    self.writePhasedata(f, df_file_data, df_file_results)

            if len(self.data)> 0:
                # Create dataframe with dict in one hist - more efficient
                self.df = pd.DataFrame.from_dict(self.data)
                msg = "COSMED Data Load completed: %d files [%d rows]" % (len(self.files),len(self.df))
                print(msg)
                logging.info(msg)
                #output dataframe to csv
                now = datetime.now()
                outputfile = 'cosmed_xnatupload_' + now.strftime('%Y%m%d') + '.csv'
                self.df.to_csv(join(self.inputdir, outputfile), index=False)
                msg = 'COSMED data file generated: %s' % join(self.inputdir, outputfile)
                logging.info(msg)
                rtn = True
            else:
                raise ValueError("Error: Data load failed")
        except Exception as e:
            print(len(self.data), ' files loaded')
            if f is not None:
                msg = 'ERROR in File: %s - %s' % (f, e)
            else:
                msg = e
            logging.error(msg)
            print(msg)
        finally:

            return rtn

    def extractLevel(self, dataval):
        """
        convert LEVEL_X to integer
        :param dval:
        :return:
        """
        # dataval = row['Dyspnea']
        if (isinstance(dataval, str) or isinstance(dataval, unicode)) and dataval.startswith('LEVEL'):
            dval = dataval.split("_")
            return int(dval[1])

    def parseFilename(self, filename):
        """
        Splits filename to get information
        EXPECTS: 1022BB_6MonthD_30sec_20170918.xlsx
        MAY GET: 1022BB_6MonthD_20170918.xlsx - OK
        or 1022_6MonthD_20170918.xlsx - not ok
        If syntax is wrong - this will fail TODO: replace with regex
        :param filename:
        :return:
        """
        pattern = '^(\d{4}\S{2})_(\d{1,2}).*(\d{8})\.xlsx$'
        m = re.search(pattern,filename)
        if m is not None:
            self.data['SubjectID'].append(m.group(1))
            self.data['interval'].append(m.group(2))
            self.data['date'].append(m.group(3))
            self.data['filename'].append(filename)
        # fparts = filename.split("_")
        # if len(fparts) == 4:
        #     # split to ID, interval, date
        #     self.data['SubjectID'].append(fparts[0])
        #     self.data['interval'].append(fparts[1][0])
        #     self.data['date'].append(fparts[3][0:8])
        #     self.data['filename'].append(filename)
            results = [self.data[f][-1] for f in ['SubjectID', 'interval', 'date', 'filename']]
            msg = 'Filedata: %s' % ",".join(results)
            logging.debug(msg)
        else:
            logging.error('Filename syntax is different: %s', filename)
            results= None
        return results

    def parseProtocol(self, df_results, df_data_ex, fieldnames):
        """
        Load protocol data
        :param df_results:
        :param df_data_ex:
        :param fieldnames:
        :return:
        """
        for field in fieldnames[0:3]:
            max = df_results[df_results['Parameter'] == field]['Max'].values[0]
            if max is None:
                max = ''
            if isinstance(max, time):
                max = max.hour * 60 + max.minute + float(max.second) / 60
            # data.append(max)
            self.data[field].append(max)

        # One field (Dyspnea - Borg) is in data tab not results
        field = fieldnames[3]
        dataval = df_data_ex[field].iloc[-1]
        self.data[field].append(dataval)
        loadeddata = [self.data[f][-1] for f in fieldnames]
        # logging.debug("Proto:",loadeddata)
        return loadeddata

    def parseMetabolic(self, df_data, fieldnames):
        """
        Load metabolic data
        :param df_data:
        :param fieldnames:
        :return:
        """
        for field in fieldnames:
            max = df_data[df_data['Parameter'] == field]['Max'].values[0]
            if max is None:
                max = ''
            self.data[field].append(max)
        loadeddata = [self.data[f][-1] for f in fieldnames]
        # logging.debug("Metab:",loadeddata)
        return loadeddata

    def parseCardio(self, df_data, fieldnames):
        """
        Load cardio data
        :param df_data:
        :param fieldnames:
        :return:
        """
        for field in fieldnames:
            max = df_data[field].iloc[-1]
            if max is None or (isinstance(max, float) and np.isnan(max)):
                max = ''
            self.data[field].append(max)
        loadeddata = [self.data[f][-1] for f in fieldnames]
        # logging.debug('Cardio:', loadeddata)
        return loadeddata

    def calcRecovery(self, df_ex, df_data):
        """
        Get Recovery data fields
        :param df_ex: Exercise data subset
        :param df_data: Recover data subset
        :return: [HRR1,HRR3,HRR5]
        """
        fields = {1: 'HRR1', 5: 'HRR3', 9: 'HRR5'}
        if df_ex.empty or df_data.empty:
            for field in fields.itervalues():
                self.data[field].append('')
        else:
            t0 = df_data['t'].iloc[0]
            t1 = df_data['t'].iloc[1]
            dt = (t1.minute * 60 + t1.second) - (t0.minute * 60 + t0.second)
            if dt == 30:
                tvals = [1, 5, 9]
            elif dt ==60:
                tvals = [1,3,5]
            else:
                print('time diff=', dt, 's')
                tvals = [1,3,5] * int(dt/60)

            d0 = df_ex['HR'].iloc[-1]
            for i in tvals:
                if i < len(df_data['HR']):
                    d1 = df_data['HR'].iloc[i]
                    d = d0 - d1
                else:
                    d=''
                self.data[fields[i]].append(d)
        loadeddata = [self.data[f][-1] for f in fields.itervalues()]
        logging.debug('Recovery: %s', loadeddata)
        return loadeddata

    def parseEfficiency(self, df_data, sid, intervals):
        """
        Get Efficiency data fields
        :param df_data: Separate file VO2data
        :param sid: subject id
        :param intervals: [col_start, col_end]
        :return:
        """
        row = df_data[df_data['SubjectID'] == sid]
        if not row.empty:
            data = row.iloc[:, intervals[0]:intervals[1]].values.tolist()[0]
            if len(data) == 0:
                data = ['', '', '']
        else:
            data = ['', '', '']

        self.data['VeVCO2 Slope'].append(data[0])
        self.data['VEVCO2 intercept'].append(data[1])
        self.data['OUES'].append(data[2])
        logging.debug("Efficiency: %s",data)
        return data

    def getTimesIntervals(self, row, n):
        """
        Apply function - use with df.apply(lambda t: getTimes(t,3), axis=1)
        :param t:
        :param n:
        :return:
        """
        t = row['t']
        return ((t.minute * 60 + t.second) % (n * 60) == 0)

    def getRowt(self, row, val):
        return (row['t'] == val)

    def updateRowVal(self, col, hdr):
        """
        update values with adjusted values
        :param col:
        :param hdr:
        :return:
        """
        for f in hdr['Parameter']:
            if isinstance(f, float) and np.isnan(f):
                continue
            if f in col.columns:
                i0 = col[f].values[0]
                r = hdr[hdr['Parameter'] == f].values[0][1]
                if isinstance(r, float) and np.isnan(r):
                    continue
                d = {col[f].iloc[0]: r}  # ignore warning as doesn't work with iloc or loc
                col[f].replace(d, inplace=True)
                msg = f, "=", i0, '[', type(i0), '] updated TO ', col[f].iloc[0], '[', type(col[f].iloc[0]), "]"
                logging.debug(msg)
        return col

    def writePhasedata(self, f, df_file_data, df_file_results):
        """
        Collate Phase data and append as new tab in datafile
        :param f:
        :return:
        """
        book = None
        writer = None
        try:
            book = load_workbook(f)
            # Output to file copy
            fparts = split(f)
            f0 = join(fparts[0], 'processed', fparts[1])
            writer = pd.ExcelWriter(f0, engine='openpyxl')
            writer.book = book
            writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
            # Generate data
            df = df_file_data.drop([0, 1])  # remove empty rows
            extraphases = ['AT', 'RC', 'Max']
            phases = df['Phase'].unique().tolist() + extraphases  # list of phase names
            # Generate columns for time intervals
            for n in [3, 1]:
                df['t' + str(n)] = df.apply(lambda t: self.getTimesIntervals(t, n), axis=1)
            d3 = df[df['t3'] == True]
            d1 = df[df['t1'] == True]
            # Generate column for extra - from manual adjustments
            for ephase in extraphases:
                df[ephase] = df.apply(lambda t: self.getRowt(t, df_file_results[ephase].iloc[0]), axis=1)

            results = dict()
            cols = []
            for phase in phases:
                if phase == 'NONE':  # ?assume not included
                    continue
                if phase == 'RECOVERY':
                    d = d1[d1['Phase'] == phase]
                    colname = phase.title()
                elif phase in ['AT', 'RC', 'Max']:
                    d = df[df[phase] == True]
                    du = self.updateRowVal(d, df_file_results[['Parameter', phase]])
                    # logging.debug phase, " Updated: ", du
                    d = du
                    colname = phase
                else:
                    d = d3[d3['Phase'] == phase]
                    colname = phase.title()
                results[colname] = d[self.fields['Parameter'].tolist()[0:14]].T
                if len(d) > 1:
                    cols = cols + [colname + " " + str(c + 1) for c in range(len(d))]
                else:
                    cols.append(colname)

            r = pd.concat([results['Rest'], results['Warmup'], results['Exercise'], results['Recovery'], results['AT'],
                           results['RC'], results['Max']], join='inner', axis=1)
            logging.debug("PHASES RESULTS: %d", len(r))
            r.columns = cols
            r.to_excel(writer, "Phases")
            writer.save()
        except Exception as e:
            msg = 'File: %s - %s ' % (f, e)
            logging.error(msg)
            print(msg)
        finally:
            msg = 'Phase data DONE: %s' % fparts[1]
            logging.debug(msg)
            #print(msg)
            # if book is not None:
            #     book.close()
            # if writer is not None:
            #     writer.close()

    def sortSubjects(self):
        '''Sort data into subjects by participant ID'''

        if self.df is not None:
            sids = self.df['SubjectID'].unique()
            ids = [i for i in sids if len(i) == 6]
            intervals = range(0, 13, 3)
            for sid in ids:
                self.subjects[sid] = dict()
                data = self.df[self.df['SubjectID'] == sid]
                for i in intervals:
                    idata = data[data['interval'] == str(i)]
                    if not idata.empty:
                        self.subjects[sid][i] = idata

                logging.debug('Subject: %s with %d datasets', sid, len(self.subjects[sid]))
            logging.debug('Subjects loaded=%d', len(self.subjects))
        else:
            logging.error('Subjects not loaded')

    def getSampleid(self, sd, interval):
        """
        Generate Unique sample ID - append prefix for subtypes
        :param sd: Subject ID
        :param row: row data with unique number
        :return: id
        """
        id = 'COS_' + sd + '_' + str(interval)
        return id

    def getxsd(self):
        xsd = 'opex:cosmed'
        return xsd

    def mapData(self, row, i, xsd):
        """
        Map SWM data to row input data
        :param row: pandas series row data
        :return: data kwargs structure to load to xnat expt
        """
        vdate = datetime.strptime(row['date'].iloc[0] + " " + row['time'].iloc[0], '%Y%m%d %I:%M:%S %p')
        mandata = {
            xsd + '/interval': str(i),
            xsd + '/date': vdate.strftime("%Y.%m.%d %H:%M:%S"),
            xsd + '/sample_id': str(row.index.values[0]),  # row number in this data file for reference
            xsd + '/sample_quality': 'Good',  # default - check later if an error
            xsd + '/data_valid': 'Checked',
            xsd + '/comments': 'Max values'
        }
        motdata = {}
        intfields =self.fields['XnatField'][self.fields['Type']=='int']#['rpe', 'grade','sbp','dbp']
        for i in range(len(self.fields)):
            field = self.fields['Parameter'][i]
            xnatfield = self.fields['XnatField'][i]
            if field in row:
                d = row[field].iloc[0]
                if isinstance(d, time):
                    motdata[xsd + '/' + xnatfield] = str(d.hour * 60 + d.minute + float(d.second) / 60)
                elif isinstance(d, datetime):
                    motdata[xsd + '/' + xnatfield] = d.strftime("%Y%m%d")
                elif isinstance(d, float) and np.isnan(d):
                    motdata[xsd + '/' + xnatfield] = ''
                elif isinstance(d,float) and xnatfield in intfields.values:
                    motdata[xsd + '/' + xnatfield] = str(int(d))
                else:
                    motdata[xsd + '/' + xnatfield] = str(d)
        return (mandata, motdata)


########################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Parse MRI Analysis',
                                     description='''\
            Reads files in a directory and extracts data for upload to XNAT

             ''')
    parser.add_argument('--filedir', action='store', help='Directory containing xnatpaths.txt (paths for COSMED)', default="sampledata\\cosmed")
    parser.add_argument('--subdir', action='store', help='Full Subdirectory for individual files')
    parser.add_argument('--datafile', action='store', help='Full path to VEVCO2 file')

    args = parser.parse_args()

    inputdir = args.filedir
    inputsubdir = args.subdir
    datafile = args.datafile

    print("Input:", inputdir)
    if access(inputdir, R_OK):
        dp = CosmedParser(inputdir, inputsubdir, datafile, True)
        if dp.df.empty:
            raise ValueError("Error during compilation - data not loaded")
        xsd = dp.getxsd()
        dp.sortSubjects()

        for sd in dp.subjects:
            print('\n***********SubjectID:', sd)
            for i, row in dp.subjects[sd].items():
                sampleid = dp.getSampleid(sd, i)
                print('Sampleid: ', sampleid)
                (mandata, data) = dp.mapData(row, i, xsd)
                print('MANDATA: ', mandata)
                print('DATA: ', data)

    else:
        print("Cannot access directory: ", inputdir)
        inputdir = "..\\..\\" + inputdir
        if access(inputdir, R_OK):
            print("But can access this one: ", inputdir)
