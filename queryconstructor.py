import metadata

# constants
INITIAL_SELECT = "SELECT %s from %s"
INITIAL_INSERT = "INSERT INTO %s VALUES (%s)"
LEFTJOIN = " LEFT JOIN %s on %s.%s = %s.%s"
SEARCH = " %s ( %s %s %s ) "


class ConstructQuery():
    query = ''
    currentColumns = []

    def __init__(self, t):
        self.metaObject = t;
        self.tableName = type(t).__name__
        self.currentColumns = [self.tableName + '.' + x for x in t.get_fields()]
        self.args = []

    def setSelect(self):
        columnsString = ','.join(self.tableName + '.' + x for x in self.metaObject.get_fields())
        self.query = INITIAL_SELECT % (columnsString, self.tableName)

    def setInsert(self, values):
        valuesString = ','.join("'"+x+"'" for x in values)
        self.args = values
        self.query = INITIAL_INSERT % (self.tableName, "?, "*(len(values)-1) + "?")
        print(self.args)

    def replaceField(self, secondTableName, key1, key2, replaceKey):
        self.query += (LEFTJOIN % (secondTableName, self.tableName, key1, secondTableName, key2))
        self.currentColumns = [x if x != (self.tableName + '.' + key1) else secondTableName + '.' + replaceKey for x in
                               self.currentColumns]
        self.query = self.query.replace(self.tableName + '.' + key1, secondTableName + '.' + replaceKey, 1)

    def search(self, colName, searchWord, condition, logicalConnection):
        if (searchWord == None): return
        if len(searchWord) != 0:
            self.query += SEARCH % (
                logicalConnection, colName, condition, '?')
            self.args.append(searchWord)
            #self.args.append((searchWord,'%'+searchWord+'%')[condition == 'LIKE'])

    def order(self, orderColumn):
        if (orderColumn == None): return
        self.query += ' ORDER BY %s' % (orderColumn)
