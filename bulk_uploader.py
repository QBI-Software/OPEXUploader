from __future__ import print_function
from os.path import join, expanduser, split
from os import mkdir,access,R_OK,W_OK
from resources.dbquery import DBI
from uploader import OPEXUploader, create_parser

ROOTDATADIR = "Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata"


class BulkUploader():
    def __init__(self, uploader):
        self.uploader = uploader
        #list expts
        configdb = join('resources', 'opexconfig.db')
        dbi = DBI(configdb)
        self.expts = dbi.getRunOptions()
        self.excludes = ['mridata', 'mri', 'blood', 'acer', 'amunet', 'fmri', 'visit']

    def close(self):
        self.uploader.xnatdisconnect()


    def run(self, project,datadir):
        """
        Runs through all available expt except those in excludes
        :param datadir:
        :return:
        """

        for expt in self.expts.values():
            if len(expt)<=0:
                continue
            runoption = expt[2:]
            if runoption in self.excludes:
                continue
            print("\n\n****** BULK LOAD: ", runoption)
            datadir = join(datadir, runoption)
            (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
            msg = 'Bulk load Finished %s: matches=%d' % (runoption.upper(), len(matches))
            print(msg)

        # Run Bloods separately
        matches = []
        for blood in ['COBAS', 'MULTIPLEX']:
            datadir = join(datadir, 'blood', blood)
            (missing, matches) = self.uploader.runDataUpload(project, datadir, 'blood')
        msg = 'Bulk load Finished BLOOD: matches=%d' % len(matches)
        print(msg)
        # Run Visits
        datadir = join(datadir, 'visit')
        runoption = 'visit'
        (missing, matches) = self.uploader.runDataUpload(project, datadir, runoption)
        msg = 'Bulk load Finished VISIT: matches=%d' % len(matches)
        print(msg)


def getLogFile(self):
    logfile = join(expanduser('~'), 'logs', 'xnatupload.log')
    logdir = split(logfile)[0]
    if not access(logdir, W_OK):
        try:
            mkdir(logdir)
        except:
            raise IOError("Cannot create log file")
    return logfile

######################################################################################
if __name__ == '__main__':
    # Run through all reliable datasets
    db ='opex' #'xnat-dev-opex'
    project ='P1'
    #checks='--checks'   #TESTonly
    checks = ''
    parser = create_parser()
    if len(checks) > 0:
        args = parser.parse_args([db, project, checks])  # Test mode --checks
    else:
        args = parser.parse_args([db, project])
    uploader = OPEXUploader(args, logfile=getLogFile())
    uploader.config()
    uploader.xnatconnect()
    bulk = BulkUploader(uploader)
    bulk.run(ROOTDATADIR)
    bulk.close()
    print("***BULK LOAD COMPLETED**")
