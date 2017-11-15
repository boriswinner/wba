import metadata
import queryconstructor
import dbconnector
from flask import Flask
from flask import render_template
from flask import url_for
from flask import request

app = Flask(__name__)


@app.route("/", methods=['GET'])
def mainpage():
    dbconnector.scheduleDB.connect_to_database()
    dbconnector.scheduleDB.set_tables_list()
    return render_template("tableView.html", pickerName='tablesPicker', pickerURL=url_for('view_table'),
                           pickerElements=dbconnector.scheduleDB.tablesList)


@app.route("/view_table", methods=['GET', 'POST'])
def view_table():
    dbconnector.scheduleDB.connect_to_database()
    dbconnector.scheduleDB.set_tables_list()
    cur = dbconnector.scheduleDB.cur
    tableName = request.args.get("tablesPicker")
    t = getattr(metadata, tableName.lower())
    meta = t.get_meta()
    tableColumns = cur.execute(dbconnector.GETCOLUMNNAMES % (tableName)).fetchall()
    tableColumns = [str(i[0]).strip() for i in tableColumns]
    query = queryconstructor.ConstructQuery(tableName)
    for i in tableColumns:
        if meta[i].type == 'ref':
            query.replaceField(meta[i].refTable, i, meta[i].refKey, meta[i].refName)
    cur.execute(query.query)
    tableData = cur.fetchall()

    return render_template("tableView.html", tableName=tableName, columnNames=tableColumns, tableData=tableData,
                           pickerName='tablesPicker', pickerURL=url_for('view_table'),
                           pickerElements=dbconnector.scheduleDB.tablesList, meta=meta)
