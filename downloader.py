from xnatconnect.XnatConnector import XnatConnector
from report.report.OPEXReport import OPEXReport
from os.path import join, expanduser
import argparse

def rundownloads(database, projectcode, output):
    xnat = XnatConnector(join(expanduser('~'), '.xnat.cfg'), database)
    xnat.connect()
    subjects = xnat.getSubjectsDataframe(projectcode)
    op = OPEXReport(subjects=subjects, opexfile=join('resources', 'opex.csv'))
    op.xnat = xnat
    outputdir = output
    op.downloadOPEXExpts(projectcode=projectcode, outputdir=outputdir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='OPEX Report',
                                     description='''\
                Script for reports of QBI OPEX XNAT db
                 ''')
    parser.add_argument('database', action='store', help='select database config from xnat.cfg to connect to', default='opex-ro')
    parser.add_argument('projectcode', action='store', help='select project by code', default='P1')
    parser.add_argument('--output', action='store', help='output directory for csv files')
    args = parser.parse_args()
    print('Starting download')
    rundownloads(args.database, args.projectcode, args.output)
    print('Download complete')