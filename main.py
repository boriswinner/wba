import metadata
import queryconstructor
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
    deleteIDName = 'deleteID'
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

    #form arguments for query controls

    orderColumn = request.args.get(constants.orderPickerName)
    rowsOnPageNumber = request.args.get(constants.paginationPickerName)
    if rowsOnPageNumber is None:
        rowsOnPageNumber = constants.paginationPickerElements[0]
    searchColumn = request.args.getlist(constants.columnPickerName)
    searchString = request.args.getlist(constants.inputName)
    conditions = request.args.getlist(constants.conditionsPickerName)
    logicalConnections = ['WHERE'] + request.args.getlist(constants.logicalConnectionName)
    tableColumns = cur.execute(dbconnector.GETCOLUMNNAMES % (tableName)).fetchall()
    tableColumns = [str(i[0]).strip() for i in tableColumns]
    selectedPage = request.args.get(constants.pagePickerName)
    if selectedPage is None:
        selectedPage = 0

    #form SELECT query

    tableMetadataObject = getattr(metadata, tableName.lower())
    tableMetadataDict = tableMetadataObject.get_meta()
    selectQuery = queryconstructor.ConstructQuery(tableMetadataObject)
    selectQuery.setSelect()
    for i in tableColumns:
        if tableMetadataDict[i].type == 'ref':
            selectQuery.replaceField(tableMetadataDict[i].refTable, i, tableMetadataDict[i].refKey, tableMetadataDict[i].refName)
    for i in range(len(searchString)):
        selectQuery.search(searchColumn[i], searchString[i], conditions[i], logicalConnections[i])
    selectQuery.order(orderColumn)

    #form INSERT query

    addedValues = request.args.getlist(constants.addIntoTableInputsName)
    if (len(addedValues) > 0 and len(addedValues[0]) > 0):
        insertQuery = queryconstructor.ConstructQuery(tableMetadataObject)
        insertQuery.setInsert(addedValues)

    #form DELETE query

    deleteID = request.args.get(constants.deleteIDName)
    if deleteID is not None:
        deleteQuery = queryconstructor.ConstructQuery(tableMetadataObject)
        deleteQuery.setDelete(deleteID)

    #run queries

    try:
        if (len(addedValues) > 0 and len(addedValues[0]) > 0): cur.execute(insertQuery.query, insertQuery.args)
        if (deleteID is not None): cur.execute(deleteQuery.query, deleteQuery.args)
        cur.execute(selectQuery.query, selectQuery.args)
        tableData = cur.fetchall()
    except:
        return render_template("tableView.html", tableName=tableName,
                               tablePickerElements=dbconnector.scheduleDB.tablesList,
                               columnPickerElements=selectQuery.currentColumns,
                               selectedColumns=searchColumn,
                               selectedConditions=conditions, selectedLogicalConnections=logicalConnections,
                               selectedOrder=orderColumn, selectedStrings=searchString,
                               selectedPagination=rowsOnPageNumber, selectedPage=selectedPage, incorrectQuery = 1)

    return render_template("tableView.html", tableName=tableName, tablePickerElements=dbconnector.scheduleDB.tablesList,
                           columnPickerElements=selectQuery.currentColumns,
                           selectedColumns=searchColumn,
                           selectedConditions=conditions, selectedLogicalConnections=logicalConnections,
                           selectedOrder=orderColumn, selectedStrings=searchString,
                           selectedPagination=rowsOnPageNumber, selectedPage=selectedPage,
                           columnNames=tableColumns, tableData=tableData, meta=tableMetadataDict,
                           tableColumns=[x for x in tableColumns if tableMetadataDict[x].type != 'key'])


if __name__ == "__main__":
    app.run(debug=True)
