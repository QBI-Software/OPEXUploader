# -*- coding: utf-8 -*-
"""
XNAT Utility script: XnatOrganizeFiles
Reads directories and creates directory structure
suitable for XNAT upload

Created on Thu Mar 2 2017

@author: Liz Cooper-Williams, QBI
"""

from os import listdir, R_OK, path, mkdir, access
from os.path import isdir, join,expanduser
import argparse
import sys
import re
import glob
import shutil
import pydicom as dicom
from pydicom.filereader import InvalidDicomError, read_file
import logging

class Organizer():
    def __init__(self, inputdir, scandir, opexid=True, ignoredir=None):
        logging.basicConfig(filename=join(expanduser('~'),'logs','xnatscans.log'), level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%d-%m-%Y %I:%M:%S %p')
        #Set input directory
        if not access(inputdir, R_OK):
            raise OSError("Cannot access input directory")
        else:
            self.inputdir = inputdir
        print('Input directory: ', self.inputdir)
        #Set output scan directory
        if scandir is None:
            dirpath = path.dirname(inputdir)
            self.datapath = join(dirpath, 'sortedscans')
        #origdatapath = datapath
        elif not access(scandir, R_OK):
            raise OSError("Cannot access output scan directory")
        else:
            self.datapath = scandir
        print('Scan directory: ', self.datapath)

        # Check only subject dirs processed
        self.opexid = opexid
        if self.opexid:
            self.pattern = re.compile('^\d{4}[A-Za-z0-9]+$')
        else:
            self.pattern = re.compile('[A-Za-z0-9\_\.\-]+')

        # Ignore these directories already processed - allows for repeated parsing over same dir
        if ignoredir is not None:
            self.ignorefiles = listdir(ignoredir)
            msg = 'Ignoring %d files in %s' % (len(self.ignorefiles), ignoredir)
            print(msg)
            logging.info(msg)
        else:
            self.ignorefiles = []

    def run(self):
        # Create MRI sessions for each subject directory
        datapath = self.datapath
        series = {}
        for subject in listdir(self.inputdir):
            msg = "Subject: %s" % subject
            logging.info(msg)
            print(msg)
            if self.opexid and len(subject) == 8:
                trimsubject = subject[0:6]
            else:
                trimsubject = subject
            if not self.pattern.match(subject) or subject in self.ignorefiles or trimsubject in self.ignorefiles:
                msg = "Not a subject or marked for ignore - next"
                logging.warning(msg)
                print(msg)
                continue
            try:
                mkdir(join(datapath, subject))
                mkdir(join(datapath, subject, 'scans'))
                datapath = join(datapath, subject, 'scans')
            except OSError as e:
                msg = 'Directory exists: %s' % e.args[0]
                logging.info(msg)
                print(msg)
                datapath = self.datapath
                continue

            for group in listdir(join(self.inputdir, subject)):
                grouppath = join(self.inputdir, subject, group)
                if not isdir(grouppath) or group == 'scans':
                    continue
                # get list of series
                for filename in listdir(grouppath):
                    try:
                        dcm = dicom.read_file(join(grouppath, filename))
                    except InvalidDicomError:
                        msg = "Not DICOM - skipping: %s" % filename
                        logging.warning(msg)
                        print(msg)
                        continue
                    series_num = str(dcm.SeriesNumber)
                    if series_num not in series:
                        parts = filename.split(".")
                        idx = parts.index(series_num.zfill(4))
                        series_prefix = '.'.join(parts[0:idx + 1])
                        series[series_num] = [join(datapath, str(int(series_num))), series_prefix]
                # Move files to new dirs grouped by series

                for snum, dpath in series.items():
                    seriespattern = dpath[1] + '.*'
                    try:
                        mkdir(dpath[0])
                        files = glob.glob(join(grouppath, seriespattern))
                        for f2 in files:
                            shutil.copy(f2, dpath[0])
                    except:
                        msg = "Error copying files: %s" % dpath
                        logging.error(msg)
                        print(msg)
                        break
                        # raise OSError

                series = {}

            msg = "Files sorted to dir: %s" % datapath
            logging.info(msg)
            print(msg)
            datapath = self.datapath
        return True

if __name__ == "__main__":
    # Read dirlist until get to *.dcm or *.IMA
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
            Reads directories and creates directory structure suitable for XNAT upload
            - expects this input dir format: SUBJECTID/Group/*.IMA (mixed series)
            - note this will not work if directory structure is different.
            - outputs format: sortedscans/SUBJECTID/scans/series/*.IMA
            - EXAMPLE: (where data/raw contains SUBJECTID folders)
            python XnatOrganizeFiles.py "data/raw" --scandir "data/sortedscans"

             ''')
    parser.add_argument('--inputdir', action='store', help='Top level file directory eg SUBJECTID', default="sampledata\\mri")
    parser.add_argument('--scandir', action='store', help='Copy scans to this directory for upload to XNAT', default="sampledata\\mri\\sortedscans")
    parser.add_argument('--opexid', action='store_true', help='SUBJECTID directories in OPEX format eg 1001DS', default='True')
    parser.add_argument('--ignore', action='store', help='Ignore already processed - allows for repeated parsing over same dir (eg "done")')
    args = parser.parse_args()

    org = Organizer(args.inputdir,args.scandir,args.opexid,args.ignore)
    print("ScanOrganizer loaded")
    org.run()
    print("ScanOrganizer complete")


    # series ={}
    # #pattern = '^([0-9A-Z_\.]+)(\d{4})\..*'
    # #p = re.compile(pattern)
    # #Read files from input directory
    # inputdir = args.inputdir
    # if not access(inputdir, R_OK):
    #     raise OSError("Cannot access input directory")
    #
    # #Create output directory if not already existing
    # if args.scandir is not None:
    #     datapath = args.scandir
    # else:
    #     dirpath = path.dirname(inputdir)
    #     datapath = join(dirpath, 'sortedscans')
    # origdatapath = datapath
    # #Check only subject dirs processed
    # if args.opexid is not None and args.opexid:
    #     pattern = re.compile('^\d{4}[A-Za-z0-9]+$')
    # else:
    #     pattern = re.compile('[A-Za-z0-9\_\.\-]+')
    # #Ignore these directories already processed - allows for repeated parsing over same dir
    # if args.ignore is not None and args.ignore:
    #     ignorefiles = listdir(args.ignore)
    #     msg = 'Ignoring %d files in %s' % (len(ignorefiles), args.ignore)
    #     print(msg)
    #     logging.info(msg)
    # else:
    #     ignorefiles=[]
    # #Create MRI sessions for each subject directory
    # for subject in listdir(inputdir):
    #     msg = "Subject: %s" % subject
    #     logging.info(msg)
    #     print(msg)
    #     if args.opexid is not None and args.opexid and len(subject) == 8:
    #         trimsubject = subject[0:6]
    #     else:
    #         trimsubject=subject
    #     if not pattern.match(subject) or subject in ignorefiles or trimsubject in ignorefiles:
    #         msg= "Not a subject or marked for ignore - next"
    #         logging.warning(msg)
    #         print(msg)
    #         continue
    #     try:
    #         mkdir(join(datapath, subject))
    #         mkdir(join(datapath,subject,'scans'))
    #         datapath = join(datapath,subject,'scans')
    #     except OSError:
    #         msg = 'Directory exists: %s' % join(datapath, subject)
    #         logging.info(msg)
    #         print(msg)
    #         datapath = origdatapath
    #         continue
    #     for group in listdir(join(inputdir,subject)):
    #         grouppath = join(inputdir,subject,group)
    #         if not isdir(grouppath) or group == 'scans':
    #             continue
    #         # get list of series
    #         for filename in listdir(grouppath):
    #             try:
    #                 dcm = dicom.read_file(join(grouppath,filename))
    #             except InvalidDicomError:
    #                 msg = "Not DICOM - skipping: %s" % filename
    #                 logging.warning(msg)
    #                 print(msg)
    #                 continue
    #             series_num = str(dcm.SeriesNumber)
    #             if series_num not in series:
    #                 parts = filename.split(".")
    #                 idx = parts.index(series_num.zfill(4))
    #                 series_prefix = '.'.join(parts[0:idx + 1])
    #                 series[series_num] = [join(datapath,str(int(series_num))), series_prefix]
    #         # Move files to new dirs grouped by series
    #
    #         for snum, dpath in series.items():
    #             seriespattern = dpath[1] + '.*'
    #             try:
    #                 mkdir(dpath[0])
    #                 files = glob.glob(join(grouppath, seriespattern))
    #                 for f2 in files:
    #                     shutil.copy(f2, dpath[0])
    #             except:
    #                 msg = "Error copying files: %s" % dpath
    #                 logging.error(msg)
    #                 print(msg)
    #                 break
    #                 #raise OSError
    #
    #         series={}
    #
    #     msg = "Files sorted to dir: %s" % datapath
    #     logging.info(msg)
    #     print(msg)
    #     datapath = origdatapath






