import metadata

# constants
INITIAL = "SELECT %s from %s"
LEFTJOIN = " LEFT JOIN %s on %s.%s = %s.%s"
SEARCH = "( %s %s '%s' )"

class ConstructQuery():
    query = ''

    def __init__(self, t):
        self.tableName = type(t).__name__
        columnsString = ','.join(self.tableName+'.'+ x for x in t.get_fields())
        self.query = INITIAL % (columnsString, self.tableName)

    def replaceField(self, secondTableName, key1, key2, replaceKey):
        self.query += (LEFTJOIN % (secondTableName, self.tableName, key1, secondTableName, key2))
        self.query = self.query.replace(self.tableName + '.' + key1, secondTableName + '.' + replaceKey, 1)

    def search(self, colName, searchWord, condition):
        if (searchWord == None): return
        if (self.query.find("WHERE") != -1):
            self.query += ' AND '
        else:
            self.query += ' WHERE '
        if len(searchWord) != 0:
            self.query += SEARCH % (self.tableName+'.'+colName, condition, searchWord)