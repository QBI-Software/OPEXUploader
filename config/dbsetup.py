####
# Initial config database setup
#####################################
import sqlite3
import pandas

DBNAME = 'opexconfig_test.db'
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
    opex = pandas.read_csv('opex.csv')
    opex.fillna('', inplace=True)
    expts = opex['Expt'].unique()
    for expt in expts:
        info = opex[opex['Expt'] == expt]
        hasdates = 0
        if info['date_provided'].values[0] == 'y':
            hasdates = 1
        sql = "INSERT INTO expts VALUES(\'%s\',%d,%d,\'%s\',\'%s\',%d,\'%s\',\'%s\')" % (info['Expt'].values[0], info['interval'].values[0], info['total'].values[0], info['xsitype'].values[0], info['prefix'].values[0], hasdates, info['name'].values[0], info['option'].values[0])
        print sql
        c.execute(sql)

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
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    # Load fields files
    csvfiles = {'BLOOD': 'blood_fields.csv','CANTAB':'cantab_fields.csv','ASHS and Freesurfer': 'MRI_fields.csv'}
    for expt in csvfiles.keys():
        print("Loading exptfields: ", expt)
        fname = csvfiles[expt]
        df = pandas.read_csv(fname, header=0)
        # Get column name for expt
        c.execute('SELECT expt FROM expts WHERE name=?',(expt,))
        for info in c.fetchall():
            colname = info[0]
            for f in df[colname]:
                if isinstance(f, str) or isinstance(f, unicode):
                    sql = "INSERT INTO opexfields(expt,fieldname) VALUES(\'%s\',\'%s\')" % (colname,f)
                    print sql
                    c.execute(sql)
    conn.commit()
    conn.close()

def setupIDs():
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    df = pandas.read_csv('incorrectIds.csv')
    # Create table
    c.execute('''CREATE TABLE opexids
                    (incorrect TEXT, correct TEXT)''')

    for i in range(len(df)):
        sql = "INSERT INTO opexids VALUES(\'%s\',\'%s\')" % (df['INCORRECT'][i],df['CORRECT'][i])
        print sql
        c.execute(sql)
    conn.commit()
    conn.close()
    
def checkDB():
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    t = ('CANTAB',)
    c.execute('SELECT * FROM expts WHERE name=?', t)
    print("**Selecting all CANTAB**")
    print c.fetchall()
    print("**Selecting all COBAS fields")
    t = ('COBAS',)
    c.execute('SELECT fieldname FROM opexfields WHERE expt=?', t)
    print c.fetchall()

    print("**Selecting IncorrectIds**")
    c.execute('SELECT * FROM opexids')
    print c.fetchall()

    conn.close()


if __name__ == '__main__':
    """
    Initial config database setup - uncomment setup and load sqls
    """
    setupDB()
    setupFields()
    loadFields()
    setupIDs()
    checkDB()