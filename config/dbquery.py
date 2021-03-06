import sys
print(sys.version)
import sqlite3
from os.path import join
from os import access, R_OK, W_OK

class DBI():
    def __init__(self, dbfile):
        """
        Init for connection to config db
        :param dbfile:
        """
        self.dbfile = dbfile
        self.c = None

    def getconn(self):
        self.conn = sqlite3.connect(self.dbfile)
        self.c = self.conn.cursor()

    def closeconn(self):
        self.conn.close()

    def getIDs(self):
        """
        Get list of Incorrect and Correct IDs
        :return: list with tuples pairs or None if not found
        """
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT * FROM opexids")
        ids = self.c.fetchall()
        if len(ids)<=0:
            ids = None
        return ids

    def deleteIDs(self):
        """
        Delete all IDs in table
        :return:
        """
        if self.c is None:
            self.getconn()
        cnt = self.c.execute("DELETE FROM opexids").rowcount
        return cnt

    def addIDs(self,idlist):
        """
        Save changes to Incorrect and Correct IDs - all are replaced
        :param idlist:
        :return: number of ids added (total)
        """
        if self.c is None:
            self.getconn()
        self.deleteIDs()
        cnt = self.c.executemany('INSERT INTO opexids VALUES (?,?)', idlist).rowcount
        self.conn.commit()
        self.conn.close()
        return cnt

    def addFields(self, fieldslist, table):
        """
        Save changes to Incorrect and Correct IDs - all are replaced
        :param idlist:
        :return: number of ids added (total)
        """
        if self.c is None:
            self.getconn()
        cnt = self.c.executemany('INSERT INTO opexids VALUES (?,?)', idlist).rowcount
        self.conn.commit()
        self.conn.close()
        return cnt


    def getCorrectID(self,sid):
        """
        Get correct ID if it exists in lookup table
        :param sid:
        :return:
        """
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT correct FROM opexids WHERE incorrect=?",(sid,))
        data = self.c.fetchone()
        if data is not None:
            cid = data[0]
        else:
            cid = sid
        return cid

    def getRunOptions(self):
        """
        Get runoptions for dropdown
        :return: dict of runoptions
        """
        if self.c is None:
            self.getconn()
        runoptions = {}
        self.c.execute("SELECT name,option FROM expts")
        for k,val in self.c.fetchall():
            runoptions[k] = val
        self.conn.close()
        return runoptions

    def getFields(self,etype):
        """
        Returns fields for expt type as dataframe
        :param etype:
        :return:
        """
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT DISTINCT fieldname FROM opexfields WHERE expt=?", (etype,))
        data = [d[0] for d in self.c.fetchall()]
        return data

    def getInfo(self,etype):
        """
        Returns fields for expt type as dataframe
        :param etype:
        :return:
        """
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT xsitype,prefix FROM expts WHERE expt=?", (etype,))
        data = self.c.fetchall()
        if len(data) > 0:
            data = data[0]
            info = {'xsitype': data[0], 'prefix': data[1]}
        else:
            info = None

        return info

    def getExpts(self):
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT expt FROM expts")
        data = [d[0] for d in self.c.fetchall()]
        return data

    def getDatelessExpts(self):
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT expt FROM expts WHERE hasdates=0")
        data = [d[0] for d in self.c.fetchall()]
        return data

    def getXsitypeFromPrefix(self,prefix):
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT xsitype FROM expts WHERE prefix=?",(prefix,))
        data = self.c.fetchone()[0]
        return data

    def getTotal(self,exptname):
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT total FROM expts WHERE expt=?",(exptname,))
        data = self.c.fetchone()[0]
        return data

    def getInterval(self,exptname):
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT intervals FROM expts WHERE expt=?",(exptname,))
        data = self.c.fetchone()[0]
        return data

    def getExptsByName(self, name):
        if self.c is None:
            self.getconn()
        self.c.execute("SELECT expt FROM expts WHERE name=?", (name,))
        data = [d[0] for d in self.c.fetchall()]
        return data


if __name__ == "__main__":
    configdb = join('..','resources', 'opexconfig.db')
    if access(configdb,R_OK):
        dbi = DBI(configdb)
        dbi.getconn()
        ids = dbi.getIDs()
        print("IDS: ",ids)
        etypes = ['MULTIPLEX','CANTAB MOT', 'MRI FS']
        for etype in etypes:
            info = dbi.getInfo(etype)
            print(info)
            fields = dbi.getFields(etype)
            print(fields)
        visitdata = dbi.getDatelessExpts()
        print(visitdata)

    else:
        raise IOError("cannot access db")


