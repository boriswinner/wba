import metadata
import fdb
from flask import Flask
from flask import render_template
from flask import url_for
from flask import request

app = Flask(__name__)
import sys

# constants
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
            self.tablesList = [i[0] for i in self.tablesList]
            self.gotTablesList = 1


scheduleDB = DbConnection()


@app.route("/", methods=['GET'])
def mainpage():
    scheduleDB.connect_to_database()
    scheduleDB.set_tables_list()
    return render_template("tableView.html", pickerName='tablesPicker', pickerURL=url_for('view_table'),
                           pickerElements=scheduleDB.tablesList)


@app.route("/view_table", methods=['GET', 'POST'])
def view_table():
    scheduleDB.connect_to_database()
    scheduleDB.set_tables_list()
    cur = scheduleDB.cur
    tableName = request.args.get("tablesPicker")
    t = getattr(metadata, tableName.lower())
    meta = t.get_meta()
    tableColumns = cur.execute(GETCOLUMNNAMES % (tableName)).fetchall()
    tableColumns = [str(i[0]).strip() for i in tableColumns]
    query = "select * from " + tableName
    cur.execute(query)
    tableData = cur.fetchall()
    return render_template("tableView.html", tableName=tableName, columnNames=tableColumns, tableData=tableData,
                           pickerName='tablesPicker', pickerURL=url_for('view_table'),
                           pickerElements=scheduleDB.tablesList, meta=meta)
