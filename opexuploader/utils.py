import sys
from os.path import join,abspath,dirname
from os import access,R_OK
from glob import iglob
import logging

##### Global functions
def findResourceDir():
    # try local
    base = dirname(__file__)
    resource_dir = join(base, 'resources')
    if not access(resource_dir,R_OK):
        base = dirname(base)
        resource_dir = join(base, 'resources')
        if not access(resource_dir, R_OK):
            base = dirname(base)
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
                msg = 'Cannot locate resources dir: %s' % abspath(resource_dir)
                raise ValueError(msg)
    msg = 'Resources dir located to: %s ' % abspath(resource_dir)
    logging.info(msg)
    return abspath(resource_dir)