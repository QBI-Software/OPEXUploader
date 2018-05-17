import sys
from os.path import join,abspath,dirname
from os import access,R_OK
from glob import iglob
import logging

##### Global functions
def findResourceDir():
    # try local
    if sys.platform =='darwin':
        base = dirname(abspath('.'))
        resource_dir = join(base, 'resources')
    else:
        resource_dir = join('resources')
        base = dirname(abspath('..'))
    if not access(resource_dir,R_OK):
        allfiles = [y for y in iglob(join(base,'**', "resources"))]
        files = [f for f in allfiles if not 'build' in f]
        if len(files) == 1:
            resource_dir = files[0]
        elif len(files) > 1:
            for rf in files:
                if access(rf, R_OK):
                    resource_dir= rf
                    break
        else:
            raise ValueError('Cannot locate resources dir: ', abspath(resource_dir))
    logging.info('Resources dir located to: ', abspath(resource_dir))
    return abspath(resource_dir)