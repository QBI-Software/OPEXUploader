#####################################
# Initial config database setup
#####################################
import pandas
import sqlite3
from os.path import join
BASEDIR = '..'
DBNAME = join(BASEDIR, 'resources', 'opexconfig.db')

def setupDB():
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE expts 
                (expt TEXT PRIMARY KEY,
                intervals INTEGER,
                total INTEGER,
                xsitype TEXT,
                prefix TEXT,
                hasdates INTEGER,
                name TEXT,
                option TEXT)
                ''')

    # Read from local files
    opex = pandas.read_csv(join(BASEDIR, "resources", 'fields', 'opex.csv'))
    opex.fillna('', inplace=True)
    expts = opex['Expt'].unique()
    for expt in expts:
        info = opex[opex['Expt'] == expt]
        hasdates = 0
        if info['date_provided'].values[0] == 'y':
            hasdates = 1
        sql = "INSERT INTO expts VALUES(\'%s\',%d,%d,\'%s\',\'%s\',%d,\'%s\',\'%s\')" % (
        info['Expt'].values[0], info['interval'].values[0], info['total'].values[0], info['xsitype'].values[0],
        info['prefix'].values[0], hasdates, info['name'].values[0], info['option'].values[0])
        print sql
        c.execute(sql)

    # Save (commit) the changes
    conn.commit()

    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()

def updateDB():
    """
    Enter new data in opex.csv then run this command
    Will check for existence of expt type first (so if modifying fields, delete this first)
    :return:
    """
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    # Read from local files
    opex = pandas.read_csv(join(BASEDIR, "resources", 'fields', 'opex.csv'))
    opex.fillna('', inplace=True)
    expts = opex['Expt'].unique()
    for expt in expts:
        c.execute('SELECT * FROM expts WHERE expt=?', (expt,))
        if len(c.fetchall()) <= 0:
            info = opex[opex['Expt'] == expt]
            hasdates = 0
            if info['date_provided'].values[0] == 'y':
                hasdates = 1
            sql = "INSERT INTO expts VALUES(\'%s\',%d,%d,\'%s\',\'%s\',%d,\'%s\',\'%s\')" % (
                info['Expt'].values[0], info['interval'].values[0], info['total'].values[0], info['xsitype'].values[0],
                info['prefix'].values[0], hasdates, info['name'].values[0], info['option'].values[0])
            print sql
            c.execute(sql)
        else:
            continue

    # Save (commit) the changes
    conn.commit()

    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()


def setupFields():
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE opexfields
                (expt TEXT,
                fieldname TEXT,
                longname TEXT,
                statsinclude INTEGER,
                minval REAL,
                maxval REAL, 
                difftype TEXT,
                datatype TEXT)
                ''')
    conn.commit()
    conn.close()


def loadFields():
    """
    Load data from csv files to opexfields
    Will skip if field exists
    :return:
    """
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    # Load fields files
    csvfiles = {'BLOOD': 'blood_fields.csv',
                'CANTAB': 'cantab_fields.csv',
                'ASHS and Freesurfer': 'MRI_fields.csv',
                'ASHSRaw': 'ashsraw_fields.csv',
                'FMRI': 'MRI_fields.csv',
                'COSMED': 'cosmed_fields.csv',
                'DEXA': 'dexa_fields.csv',
                'GODIN': 'godin_fields.csv',
                'DASS': 'dass_fields.csv',
                'HEALTH': 'health_fields.csv',
                'IPAQ': 'ipaq_fields.csv',
                'FITBIT': 'fitbit_fields.csv',
                'ISI and PSQI': 'insomnia_fields.csv',
                'SF36': 'sf36_fields.csv',
                'FOODDIARY': 'fooddiary_fields.csv',
                'ACCELEROMETRY': 'accel_fields.csv',
                'AMUNETALL': 'amunetall_fields.csv'
                }

    for expt in csvfiles.keys():
        print("Loading exptfields: ", expt)
        print(expt)
        fname = csvfiles[expt]
        df = pandas.read_csv(join(BASEDIR, "resources", "fields", fname), header=0)
        print(df)
        # Get column name for expt
        c.execute('SELECT expt FROM expts WHERE name=?', (expt,))
        for info in c.fetchall():
            colname = info[0]
            print(colname)
            for f in df[colname]:
                # Check that field does not already exist
                c.execute('SELECT * FROM opexfields WHERE expt=? AND fieldname=?', (colname, f,))
                if len(c.fetchall()) <= 0:
                    if isinstance(f, str) or isinstance(f, unicode):
                        sql = "INSERT INTO opexfields(expt,fieldname) VALUES(\'%s\',\'%s\')" % (colname, f)
                        print sql
                        c.execute(sql)
    conn.commit()
    conn.close()


def setupIDs():
    """
    Load incorrect IDs from csv
    IMPORTANT: Entries can be made by users in the OPEX Uploader App so only use this method if initiating a db
    OR extract entries from db and update the CSV before running
    :return:
    """
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    df = pandas.read_csv(join(BASEDIR, "resources", 'incorrectIds.csv'))

    # Create table
    c.execute('''CREATE TABLE opexids 
                    (incorrect TEXT, correct TEXT)''')

    for i in range(len(df)):
        sql = "INSERT INTO opexids VALUES(\'%s\',\'%s\')" % (df['INCORRECT'][i], df['CORRECT'][i])
        print sql
        c.execute(sql)
    conn.commit()
    conn.close()


def checkDB(expt):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    t = (expt,)
    print("**Selecting expts for  {0}**".format(expt))
    c.execute('SELECT * FROM expts WHERE name=?', t)
    print c.fetchall()
    print("**Selecting fields for  {0}**".format(expt))
    c.execute('SELECT fieldname FROM opexfields WHERE expt=?', t)
    print c.fetchall()

    print("**Selecting IncorrectIds**")
    c.execute('SELECT * FROM opexids')
    print c.fetchall()

    conn.close()


def deleteTable(expt):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    c.execute('DROP TABLE {};'.format(expt))
    conn.commit()


def readTable(expt):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    df = pandas.read_sql_query('SELECT * FROM {}'.format(expt), conn)
    return df



if __name__ == '__main__':
    """
    Initial config database setup - or update new types
    Run with `python dbsetup.py`
    """
    input = raw_input("Do you want to initialize or just update the config database? initialize [i] or update [u]: ")
    if input.lower() == 'u':
        update = True
    else:
        update = False

    if not update:
        print('Initializing config database')
        # 1. Create expts table
        # Delete table if exists - to prevent duplicate entries
        deleteTable('expts')
        setupDB()
        # 2. Create opexfields table and load data
        deleteTable('opexfields')
        setupFields()
        loadFields()
        # 3. Create opexids (Incorrect IDs to replace) - do not run if already exists as can be edited by users
        deleteTable('opexids')
        setupIDs()
        # 4. Check database tables
        checkDB('HEALTH')
    else:
        # Update only
        print('Updating config database')
        updateDB()
        loadFields()


