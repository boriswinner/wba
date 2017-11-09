import fdb
from flask import Flask
from flask import render_template
from flask import request
app = Flask(__name__)

#constants
GETTABLES = """SELECT a.RDB$RELATION_NAME
    FROM RDB$RELATIONS a
    WHERE RDB$SYSTEM_FLAG = 0 AND RDB$RELATION_TYPE = 0
        """

class dbConnection:
    connected = 0
    def connectToDatabase(self):
        if (not self.connected):
            self.con = fdb.connect(dsn='BASE.FDB', user='sysdba', password='masterkey', charset='UTF8')
            self.cur = self.con.cursor()
            self.connected = 1

sheduleDB = dbConnection()

def getTableColumns(table, cur):
    query = """select rdb$field_name 
from rdb$relation_fields
where rdb$relation_name= '""" + table + "'"
    cur.execute(query)
    return cur.fetchall()

@app.route("/", methods = ['GET'])
def mainpage():
    sheduleDB.connectToDatabase()
    cur = sheduleDB.cur
    cur.execute(GETTABLES)
    tables = cur.fetchall()
    tablesList = []
    for i in tables:
        tablesList.append(str(i)[2:-4])
    return render_template("picker.html", tables=tablesList)

@app.route("/view_table", methods=['GET', 'POST'])
def viewTable():
    tableName = request.args.get("tablespicker")
    header = "<h1>Viewing table: " + tableName + "</h1>"
    sheduleDB.connectToDatabase()
    cur = sheduleDB.cur
    tableColumns = getTableColumns(tableName, cur)
    query = "select * from " + tableName
    cur.execute(query)
    tableData = cur.fetchall()
    tableDataString = ""
    for i in tableColumns:
        tableDataString += str(i) + '\r\n'
    for i in tableData:
        tableDataString += str(i) + '\r\n'
    return mainpage() + header + '<pre>' + '\r\n' + tableDataString + '</pre>'
