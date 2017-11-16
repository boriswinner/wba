import metadata

# constants
INITIAL = "SELECT %s from %s"
LEFTJOIN = " LEFT JOIN %s on %s.%s = %s.%s"


class ConstructQuery():
    query = ''

    def __init__(self, tableName):
        self.tableName = tableName
        t = getattr(metadata, tableName.lower())
        columns = t.get_fields()
        columnsString = ','.join([tableName+'.'+str(x) for x in columns])
        self.query = INITIAL % (columnsString, tableName)

    def replaceField(self, secondTableName, key1, key2, replaceKey):
        self.query += (LEFTJOIN % (secondTableName, self.tableName, key1, secondTableName, key2))
        self.query = self.query.replace(self.tableName + '.' + key1, secondTableName + '.' + replaceKey, 1)