import sqlite3
import pandas

class DBI():
    def __init__(self, dbfile):
        #connect to config db
        self.dbfile = dbfile
        self.dbi = None

    def getconn(self):
        self.conn = sqlite3.connect(self.dbfile)
        self.dbi = self.conn.cursor()

    def closeconn(self):
        self.conn.close()

    def getIDs(self):
        if self.dbi is None:
            self.getconn()
        self.dbi.execute("SELECT * FROM opexids")
        ids = self.dbi.fetchall()
        return ids

    def deleteIDs(self):
        if self.dbi is None:
            self.getconn()
        self.dbi.execute("DELETE FROM opexids")
        return self.getIDs()

    def addIDs(self,idlist):
        if self.dbi is None:
            self.getconn()
        olddata = self.getIDs()
        print("Rows: ", len(olddata))
        self.deleteIDs()
        cnt = 0
        for val1,val2 in idlist:
            sql = "INSERT INTO opexids VALUES(\'%s\',\'%s\')" % (val1,val2)
            #print(sql)
            cnt = self.dbi.execute(sql)
        self.conn.commit()



    def getRunOptions(self):
        self.conn = sqlite3.connect(self.dbfile)
        self.dbi = self.conn.cursor()
        runoptions = {}
        self.dbi.execute("SELECT name,option FROM expts")
        for k,val in self.dbi.fetchall():
            runoptions[k] = val
        self.conn.close()
        return runoptions