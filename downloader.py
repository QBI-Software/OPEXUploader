from xnatconnect.XnatConnector import XnatConnector
from report.report import OPEXReport
from os.path import join, expanduser
import argparse

def rundownloads(database, projectcode, output):
    xnat = XnatConnector(join(expanduser('~'), '.xnat.cfg'), database)
    xnat.connect()
    subjects = xnat.getSubjectsDataframe(projectcode)
    op = OPEXReport(subjects=subjects)
    op.xnat = xnat
    outputdir = output
    op.downloadOPEXExpts(projectcode=projectcode, outputdir=outputdir, deltas=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='OPEX Report',
                                     description='''\
                Script for reports of QBI OPEX XNAT db
                 ''')
    parser.add_argument('database', action='store', help='Database config from xnat.cfg', default='opex-ro')
    parser.add_argument('projectcode', action='store', help='select project by code', default='P1')
    parser.add_argument('--output', action='store', help='output directory for csv files', default="sampledata\\reports")
    args = parser.parse_args()
    print('Starting download')
    rundownloads(args.database, args.projectcode, args.output)
    print('Download complete')