import logging
from os import access, R_OK, getcwd
from os.path import join, abspath, dirname


##### Global functions
from config.dbquery import DBI


def findResourceDir():
    # resource dir is at top level of cwd
    base = getcwd()
    logging.debug('Base:', base)
    resource_dir = join(base, 'resources')
    ctr = 0
    # loop up x times
    while(ctr < 5 and not access(resource_dir,R_OK)):
        base = dirname(base)
        logging.debug('Base:', base)
        resource_dir = join(base, 'resources')
        ctr += 1
    # if still cannot find - raise error
    if not access(resource_dir,R_OK):
        msg = 'Cannot locate resources dir: %s' % abspath(resource_dir)
        raise ValueError(msg)
    else:
        msg = 'Resources dir located to: %s ' % abspath(resource_dir)
        logging.info(msg)
    return abspath(resource_dir)


def directory_names_for_blood_samples():
    """
    Get a list of the required directory names for detecting type of Blood sample
    :return: list of names
    """
    resource_dir = findResourceDir()
    configdb = join(resource_dir, 'opexconfig.db')
    if not access(configdb, R_OK):
        print(configdb)
        raise IOError('Cannot find config database {}'.format(configdb))
    try:
        dbi = DBI(configdb)
        expts = dbi.getExptsByName('BLOOD')
        return expts
    except Exception as e:
        raise e