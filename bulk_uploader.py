from __future__ import print_function
from os.path import join, expanduser
from resources.dbquery import DBI
from uploader import OPEXUploader, create_parser

ROOTDATADIR = "Q:\\DATA\\DATA ENTRY\\XnatUploaded\\sampledata"


class BulkUploader():
    def __init__(self, db, proj,checks=''):
        parser = create_parser()
        if len(checks) > 0:
            args = parser.parse_args([db,proj,checks]) #Test mode --checks
        else:
            args = parser.parse_args([db, proj])
        uploader = OPEXUploader(args)
        uploader.config()
        uploader.xnatconnect()
        self.uploader = uploader

    def close(self):
        self.uploader.xnatdisconnect()

######################################################################################
if __name__ == '__main__':
    # Run through all reliable datasets
    db ='xnat-dev-opex'
    project ='P1'
    #checks='--checks'   #TESTonly
    checks = ''

    bulk = BulkUploader(db,project,checks)
    configdb = join('resources', 'opexconfig.db')
    dbi = DBI(configdb)
    expts = dbi.getRunOptions()
    excludes =['mridata', 'mri','blood','acer','amunet','fmri','psqi','visit']
    for expt in expts.values():
        runoption = expt[2:]
        if runoption in excludes:
            continue
        print("BULK LOAD: ", runoption)
        datadir= join(ROOTDATADIR, runoption)
        (missing, matches) = bulk.uploader.runDataUpload(project, datadir, runoption)
        msg = 'Bulk load Finished %s: matches=%d' % (runoption.upper(),len(matches))
        print(msg)

    # Run Bloods separately
    matches=[]
    for blood in ['COBAS','MULTIPLEX']:
        datadir = join(ROOTDATADIR, 'blood', blood)
        (missing, matches) = bulk.uploader.runDataUpload(project, datadir, 'blood')
    msg = 'Bulk load Finished BLOOD: matches=%d' % len(matches)
    print(msg)
    # Run Visits
    datadir = join(ROOTDATADIR, 'visit')
    runoption = 'visit'
    (missing, matches) = bulk.uploader.runDataUpload(project, datadir, runoption)
    msg = 'Bulk load Finished VISIT: matches=%d' % len(matches)
    print(msg)

    bulk.close()
    print("***BULK LOAD COMPLETED**")
