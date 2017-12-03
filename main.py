import metadata
import queryconstructor
import dbconnector
from flask import Flask
from flask import render_template
from flask import url_for
from flask import request

app = Flask(__name__)


class Constants:
    def isField(self, i):
        return (not callable(getattr(self, i)) and not i.startswith("__"))

    def get_constants(self):
        result = {}
        for i in dir(self):
            if self.isField(i):
                result[i] = getattr(self, i)
        return result

    tablePickerName = 'tablesPicker'
    columnPickerName = 'columnsPicker'
    orderPickerName = 'orderPicker'
    paginationPickerName = 'paginationPicker'
    pagePickerName = 'pagePicker'
    conditionsPickerName = 'condition'
    logicalConnectionName = 'logicalConnection'
    inputName = 'searchString'
    formButtonText = 'View Table'
    conditions = ['LIKE', '>', '<', '>=', '<=', 'IN']
    logicalConnections = ['AND', 'OR']
    paginationPickerElements = ['5','10','20','50','100']


constants = Constants()


@app.context_processor
def inject_globals():
    return constants.get_constants()


@app.route("/", methods=['GET'])
def mainpage():
    dbconnector.scheduleDB.connect_to_database()
    dbconnector.scheduleDB.set_tables_list()
    return render_template("tableView.html", formURL=url_for('view_table'),
                          tablePickerElements=dbconnector.scheduleDB.tablesList)


@app.route("/view_table", methods=['GET', 'POST'])
def view_table():
    dbconnector.scheduleDB.connect_to_database()
    dbconnector.scheduleDB.set_tables_list()
    cur = dbconnector.scheduleDB.cur
    tableName = request.args.get(constants.tablePickerName)
    searchColumn = request.args.getlist(constants.columnPickerName)
    searchString = request.args.getlist(constants.inputName)
    orderColumn = request.args.get(constants.orderPickerName)
    selectedPagination = request.args.get(constants.paginationPickerName)
    selectedPage = request.args.get(constants.pagePickerName)
    condition = request.args.getlist(constants.conditionsPickerName)
    logicalConnections = ['WHERE'] + request.args.getlist(constants.logicalConnectionName)
    t = getattr(metadata, tableName.lower())
    meta = t.get_meta()
    tableColumns = cur.execute(dbconnector.GETCOLUMNNAMES % (tableName)).fetchall()
    tableColumns = [str(i[0]).strip() for i in tableColumns]
    query = queryconstructor.ConstructQuery(t)
    for i in tableColumns:
        if meta[i].type == 'ref':
            query.replaceField(meta[i].refTable, i, meta[i].refKey, meta[i].refName)
    for i in range(len(searchString)):
        query.search(searchColumn[i], searchString[i], condition[i], logicalConnections[i])
    query.order(orderColumn)
    print(query.query)
    print(query.args)
    cur.execute(query.query, query.args)
    tableData = cur.fetchall()

    return render_template("tableView.html", tableName=tableName, selectedColumns=searchColumn,
                           selectedConditions=condition, selectedLogicalConnections=logicalConnections,
                           selectedOrder=orderColumn, selectedStrings=searchString, columnNames=tableColumns, selectedPagination = selectedPagination, selectedPage = selectedPage,
                           tableData=tableData,
                           tablePickerElements=dbconnector.scheduleDB.tablesList,
                           columnPickerElements=query.currentColumns,
                           formURL=url_for('view_table'), meta=meta)

if __name__ == "__main__":
    app.run(debug=True)