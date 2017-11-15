import dbconnector

# constants
INITIAL = "SELECT %s from %s"
LEFTJOIN = " LEFT JOIN %s on %s.%s = %s.%s"

class ConstructQuery():
    query = ''
    def __init__(self, tableName):
        self.tableName = tableName
        tables = dbconnector.scheduleDB.cur.execute(dbconnector.GETCOLUMNNAMES % tableName).fetchall()
        tables = [str(i[0]).strip() for i in tables]
        tables = str(tables).replace('[', tableName+'.')
        tables = str(tables).replace(']', '')
        tables = str(tables).replace(" '", tableName+'.')
        tables = str(tables).replace("'", '')
        self.query = INITIAL % (str(tables), tableName)
    def replaceField(self, secondTableName, key1, key2, replaceKey):
        self.query += (LEFTJOIN % (secondTableName, self.tableName, key1, secondTableName, key2))
        self.query = self.query.replace(self.tableName+'.'+key1,secondTableName+'.'+replaceKey, 1)

