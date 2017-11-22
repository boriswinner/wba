import fdb

GETTABLES = """SELECT a.RDB$RELATION_NAME
    FROM RDB$RELATIONS a
    WHERE RDB$SYSTEM_FLAG = 0 AND RDB$RELATION_TYPE = 0"""
GETCOLUMNNAMES = """select rdb$field_name 
from rdb$relation_fields
where rdb$relation_name= '%s'"""


class DbConnection:
    connected = 0
    gotTablesList = 0

    def connect_to_database(self):
        if (not self.connected):
            self.con = fdb.connect(dsn='BASE.FDB', user='sysdba', password='masterkey', charset='UTF8')
            self.cur = self.con.cursor()
            self.connected = 1

    def set_tables_list(self):
        if (not self.gotTablesList):
            self.tablesList = self.cur.execute(GETTABLES).fetchall()
            self.tablesList = [i[0].strip() for i in self.tablesList]
            self.gotTablesList = 1


scheduleDB = DbConnection()
