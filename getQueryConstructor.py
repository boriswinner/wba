#constants

#INITIAL_SELECT = '/'

class ConstructGetQuery():
    query = ''

    def addParam(self, param, val):
        self.query += '?%s=%s' % (str(param), str(val))
        return self.query
