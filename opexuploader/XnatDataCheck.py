"""

TITLE:      deletes experiments
@author:    Alan Ho
@description:   This checks whether the subject should have data on xnat depending on whether they have
                data in the group share drive

"""
import os

import numpy as np
import pandas as pd
import time
import sys
import argparse
from os.path import join, expanduser

from xnatconnect.XnatConnector import XnatConnector


class XnatCheck(XnatConnector):
    def __init__(self, rootdir, xsd, *args):
        XnatConnector.super(*args)
        self.connect()
        self.rootdir = rootdir

    def checkSubjects(self):

        # create a unique list of subjects and interval extracted from experiment
        conn = xnat.func()
        # query_statement
        subjinterval = pd.DataFrame({'Subject':0, 'interval':0})


        # single sheet spreadsheet
        if xsd in ['acer', 'dass']:
            pass

            seriespattern = "*.xlsx"
            inputfile = join(self.rootdir, seriespattern)
            xl = pd.read_excel(inputfile)

        # multiple sheet spreadsheet
        elif xsd in ['godin']:
            xl = join()


        # by filename

        os.listdir()




        # self.rootdir







if __name__ == '__main__':


    home = expanduser("~")
    configfile = join(home, '.xnat.cfg')

    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
              Deletes experiments from Xnat

               ''')

    parser.add_argument('database', help='select database to connect to [qbixnat|irc5xnat]')
    parser.add_argument('projectcode', help='select project by code eg QBICC')

    parser.add_argument('--config', action='store', help='database configuration file (overrides ~/.xnat.cfg)')
    parser.add_argument('--filepath', action='store', help='Path to file containing expts to remove',
                        default="Q:\\DATA\\expts_removed.xlsx")
    parser.add_argument('--expt', action='store', help='Expt (sheet) containing expts to remove',
                        default="0")

    args = parser.parse_args()

    pathtofile = args.filepath
    xnat = XnatConnector(configfile, args.database)
    xnat.connect()

    print('Welcome to Xnat deleter: any shitty text-based adventure \n')
    print('It seems you have shitty data that you wish to remove')
    single = input('Removing (s)ingle or (b)atch of expts?')

    if single == 's':
        print('So you wish to only remove one experiment? Put in your expt ID tag now')
        expttag = input('Experiment ID: ')
        time.sleep(1)
        print('\nNow before going ahead, are you sure you are not high on drugs?')
        time.sleep(2)
        print('Because deleting data is permanent!')
        time.sleep(2)
        print('Sure you can reupload but you have to write like one line of code')
        time.sleep(2)
        print('Seriously, think about what you are doing to this poor innocent data!')
        time.sleep(2)
        print('What did this data ever do to you? \n')
        time.sleep(2)
        single_remove = input("Are you sure you wish to remove: {}? (y/n)".format(expttag))

        if single_remove == 'y':
            print('Okay - my wish is your command, you data murderer')
            time.sleep(2)
            print('Now, are you sure you are not high on drugs? No meth or anything?')
            time.sleep(2)
            print('Because if you are, you can tell me. Seriously, I am low in supply. Hook a brother up.')
            time.sleep(2)
            single_remove2 = input('Are you really really sure you want to delete {} (y/n) '.format(expttag))
            if single_remove2 == 'y':
                print(('Okay, deleting {} **************'.format(expttag)))


            else:
                print('okay see ya')

        elif single_remove == 'n':
            print('Okay, so you are high on drugs but you are self-aware enough to realise you have a problem')
            time.sleep(1)
            print('I won\'t delete any data until you finish your rehab')
            pass

    elif single == 'b':
        print('Okay - so you have decided to do massive deletions of your data?')
        batch_type = input('Please tell me from which experiment you wish to remove? ')
        print(('You have chosen {}'.format(batch_type)))
        print(('Aren\'t you a big man for attacking poor old defenseless {}'.format(batch_type)))
        print('\nSo these are the expt IDs you wish to remove: ')
        expts_list = pd.read_excel(pathtofile, sheetname=batch_type)
        print((expts_list['Label']))

        xsd = 'opex:' + batch_type

        batch_remove = input('Are you sure you wish to remove the following experiments? (y/n) ')

        if batch_remove == 'y':
            for i, row in expts_list[['Subject','Label']].iterrows():
                subj = xnat.conn.select('/project/P1/subject/{}'.format(row['Subject']))
                print((row['Label']))
                expt = subj.experiment(row['Label'])
                if expt.exists():
                    print(('Deleting Experiment {}'.format(row['Label'])))
                    expt.delete()
                    print(('Experiment exists: ' + str(expt.exists())))
                else:
                    print(('Ignoring - Experiment {} does not exist'.format(row['Label'])))




            # for e in expts_list['Label']:
            #     xnat.delete_experiments(projectcode=args.projectcode, datatype=xsd, fields='Label')

            xnat.conn.disconnect()


