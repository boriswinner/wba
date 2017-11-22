import metadata

# constants
INITIAL = "SELECT %s from %s"
LEFTJOIN = " LEFT JOIN %s on %s.%s = %s.%s"
SEARCH = "( %s %s '%s' )"

class ConstructQuery():
    query = ''
    currentColumns = []

    def __init__(self, t):
        self.tableName = type(t).__name__
        columnsString = ','.join(self.tableName+'.'+ x for x in t.get_fields())
        self.currentColumns = [self.tableName+'.' + x for x in t.get_fields()]
        self.query = INITIAL % (columnsString, self.tableName)

    def replaceField(self, secondTableName, key1, key2, replaceKey):
        self.query += (LEFTJOIN % (secondTableName, self.tableName, key1, secondTableName, key2))
        self.currentColumns = [x if x != (self.tableName + '.' + key1) else secondTableName + '.' + replaceKey for x in self.currentColumns]
        self.query = self.query.replace(self.tableName + '.' + key1, secondTableName + '.' + replaceKey, 1)

    def search(self, colName, searchWord, condition):
        if (searchWord == None): return
        if len(searchWord) != 0:
            self.query += (' AND ', ' WHERE ')[self.query.find("WHERE") == -1]
            self.query += SEARCH % (colName, condition, (searchWord, '%'+searchWord+'%')[condition == 'LIKE'])

    def order(self, orderColumn):
        if (orderColumn == None): return
        self.query += ' ORDER BY %s' % (orderColumn)