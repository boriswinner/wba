import metadata
import queryconstructor
import getQueryConstructor
import dbconnector
from flask import Flask, url_for, render_template,request

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
    addIntoTableInputsName = 'addIntoTableInput'
    formButtonText = 'View Table'
    conditions = ['LIKE', '>', '<', '>=', '<=', 'IN']
    logicalConnections = ['AND', 'OR']
    paginationPickerElements = ['5', '10', '20', '50', '100']


constants = Constants()


@app.context_processor
def inject_globals():
    return constants.get_constants()


@app.route("/", methods=['GET', 'POST'])
def view_table():
    dbconnector.scheduleDB.connect_to_database()
    dbconnector.scheduleDB.set_tables_list()
    cur = dbconnector.scheduleDB.cur
    tableName = request.args.get(constants.tablePickerName)
    if (tableName is None):
        tableName = dbconnector.scheduleDB.tablesList[0]
    orderColumnName = request.args.get(constants.orderPickerName)
    selectedPagination = request.args.get(constants.paginationPickerName)
    if selectedPagination is None:
        selectedPagination = constants.paginationPickerElements[0]
    searchColumn = request.args.getlist(constants.columnPickerName)
    searchString = request.args.getlist(constants.inputName)
    condition = request.args.getlist(constants.conditionsPickerName)
    logicalConnections = ['WHERE'] + request.args.getlist(constants.logicalConnectionName)
    selectedPage = request.args.get(constants.pagePickerName)
    if selectedPage is None:
        selectedPage = 0
    t = getattr(metadata, tableName.lower())
    meta = t.get_meta()
    tableColumns = cur.execute(dbconnector.GETCOLUMNNAMES % (tableName)).fetchall()
    tableColumns = [str(i[0]).strip() for i in tableColumns]
    query = queryconstructor.ConstructQuery(t)
    query.setSelect()
    for i in tableColumns:
        if meta[i].type == 'ref':
            query.replaceField(meta[i].refTable, i, meta[i].refKey, meta[i].refName)
    for i in range(len(searchString)):
        query.search(searchColumn[i], searchString[i], condition[i], logicalConnections[i])
    query.order(orderColumnName)
    addedValues = request.args.getlist(constants.addIntoTableInputsName);
    addIntoTableQuery = url_for('add',tableName=tableName)
    if (addIntoTableQuery is not None):
        insertQuery = queryconstructor.ConstructQuery(t);
        insertQuery.setInsert(addedValues)
        print(insertQuery.query)
        print(query.query)
        cur.execute(insertQuery.query,['1','p'])
    try:
        cur.execute(query.query, query.args)
        tableData = cur.fetchall()
    except:
        return render_template("tableView.html", tableName=tableName,
                               tablePickerElements=dbconnector.scheduleDB.tablesList,
                               columnPickerElements=query.currentColumns,
                               selectedColumns=searchColumn,
                               selectedConditions=condition, selectedLogicalConnections=logicalConnections,
                               selectedOrder=orderColumnName, selectedStrings=searchString,
                               selectedPagination=selectedPagination, selectedPage=selectedPage, incorrectQuery = 1)

    return render_template("tableView.html", tableName=tableName, tablePickerElements=dbconnector.scheduleDB.tablesList,
                           columnPickerElements=query.currentColumns,
                           selectedColumns=searchColumn,
                           selectedConditions=condition, selectedLogicalConnections=logicalConnections,
                           selectedOrder=orderColumnName, selectedStrings=searchString,
                           selectedPagination=selectedPagination, selectedPage=selectedPage,
                           columnNames=tableColumns, tableData=tableData, meta=meta, addIntoTableQuery = addIntoTableQuery,
                           tableColumns=tableColumns)

@app.route("/add", methods=['GET', 'POST'])
def add():
    dbconnector.scheduleDB.connect_to_database()
    dbconnector.scheduleDB.set_tables_list()
    cur = dbconnector.scheduleDB.cur
    tableName = request.args.get('tableName')
    tableColumns = cur.execute(dbconnector.GETCOLUMNNAMES % (tableName)).fetchall()
    tableColumns = [str(i[0]).strip() for i in tableColumns]
    return (render_template('addIntoTable.html', tableColumns = tableColumns, inputName = constants.addIntoTableInputsName))

if __name__ == "__main__":
    app.run(debug=True)
