#constants

#INITIAL = '/'

class ConstructGetQuery():
    query = ''

    def addParam(self, param, val):
        self.query += '?%s=%s' % (str(param), str(val))
        return self.query
