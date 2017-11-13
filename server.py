import fdb
from flask import Flask
from flask import render_template
from flask import url_for
from flask import request
app = Flask(__name__)

#constants
GETTABLES = """SELECT a.RDB$RELATION_NAME
    FROM RDB$RELATIONS a
    WHERE RDB$SYSTEM_FLAG = 0 AND RDB$RELATION_TYPE = 0"""
GETCOLUMNNAMES = """select rdb$field_name 
from rdb$relation_fields
where rdb$relation_name= '%s'"""

class dbConnection:
    connected = 0
    gotTablesList = 0
    def connectToDatabase(self):
        if (not self.connected):
            self.con = fdb.connect(dsn='BASE.FDB', user='sysdba', password='masterkey', charset='UTF8')
            self.cur = self.con.cursor()
            self.connected = 1
    def setTablesList(self):
        if (not self.gotTablesList):
            self.tablesList = self.cur.execute(GETTABLES).fetchall()
            self.tablesList = [i[0] for i in self.tablesList]
            self.gotTablesList = 1

sheduleDB = dbConnection()

@app.route("/", methods = ['GET'])
def mainpage():
    sheduleDB.connectToDatabase()
    sheduleDB.setTablesList()
    return render_template("index.html", pickerName = 'tablesPicker', pickerURL = url_for('viewTable'),
                           pickerElements = sheduleDB.tablesList)

@app.route("/view_table", methods=['GET', 'POST'])
def viewTable():
    sheduleDB.connectToDatabase()
    sheduleDB.setTablesList()
    cur = sheduleDB.cur
    tableName = request.args.get("tablesPicker")
    tableColumns = cur.execute(GETCOLUMNNAMES % (tableName)).fetchall()
    query = "select * from " + tableName
    cur.execute(query)
    tableData = cur.fetchall()
    return render_template("tableView.html", tableName = tableName, columnNames = tableColumns, tableData = tableData,
                           pickerName='tablesPicker', pickerURL = url_for('viewTable'),
                           pickerElements = sheduleDB.tablesList)