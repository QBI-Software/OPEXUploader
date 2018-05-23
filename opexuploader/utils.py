import sys
from os.path import join,abspath,dirname, basename
from os import access,R_OK, getcwd
from glob import iglob
import logging

##### Global functions
def findResourceDir():
    # resource dir is at top level of cwd
    base = getcwd()
    print('Base:', base)
    resource_dir = join(base, 'resources')
    ctr = 0
    while(ctr < 5 and not access(resource_dir,R_OK)):
        base = dirname(base)
        print('Base:', base)
        resource_dir = join(base, 'resources')
        ctr += 1
    #
    # if not access(resource_dir,R_OK):
    #     print('Looking for resources in subdirs')
    #     allfiles = [y for y in iglob(join(base,'**', "resources"))]
    #     files = [f for f in allfiles if not 'build' in f]
    #     if len(files) == 1:
    #         resource_dir = files[0]
    #     elif len(files) > 1:
    #         for rf in files:
    #             if access(rf, R_OK):
    #                 resource_dir= rf
    #                 break
    #     else:
    #         msg = 'Cannot locate resources dir: %s' % abspath(resource_dir)
    #         raise ValueError(msg)
    msg = 'Resources dir located to: %s ' % abspath(resource_dir)
    logging.info(msg)
    return abspath(resource_dir)