import metadata
import queryconstructor
import dbconnector
import re
from flask import Flask, url_for, render_template, request

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
    editInputName = 'editInput'
    deleteIDName = 'deleteID'
    formButtonText = 'View Table'
    conditions = ['LIKE', '>', '<', '>=', '<=', 'IN']
    logicalConnections = ['AND', 'OR']
    paginationPickerElements = ['5', '10', '20', '50', '100']


constants = Constants()


class GlobalVars:
    tableData = []
    tableDataWithoutRef = []


globalvars = GlobalVars()


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

    # form arguments for query controls

    orderColumn = request.args.get(constants.orderPickerName)
    rowsOnPageNumber = request.args.get(constants.paginationPickerName)
    if rowsOnPageNumber is None:
        rowsOnPageNumber = constants.paginationPickerElements[0]
    searchColumn = request.args.getlist(constants.columnPickerName)
    searchString = request.args.getlist(constants.inputName)
    conditions = request.args.getlist(constants.conditionsPickerName)
    logicalConnections = ['WHERE'] + request.args.getlist(constants.logicalConnectionName)
    columnNames = cur.execute(dbconnector.GETCOLUMNNAMES % (tableName)).fetchall()
    columnNames = [str(i[0]).strip() for i in columnNames]
    selectedPage = request.args.get(constants.pagePickerName)
    if selectedPage is None:
        selectedPage = 0

    # form SELECT query

    tableMetadataObject = getattr(metadata, tableName.lower())
    tableMetadataDict = tableMetadataObject.get_meta()
    selectQuery = queryconstructor.ConstructQuery(tableMetadataObject)
    selectQuery.setSelect()
    globalvars.tableDataWithoutRef = cur.execute(selectQuery.query).fetchall()
    for i in columnNames:
        if tableMetadataDict[i].type == 'ref':
            selectQuery.replaceField(tableMetadataDict[i].refTable, i, tableMetadataDict[i].refKey,
                                     tableMetadataDict[i].refName)
    for i in range(len(searchString)):
        selectQuery.search(searchColumn[i], searchString[i], conditions[i], logicalConnections[i])
    selectQuery.order(orderColumn)

    # form INSERT query

    addedValues = request.args.getlist(constants.addIntoTableInputsName)
    if (len(addedValues) > 0 and len(addedValues[0]) > 0):
        insertQuery = queryconstructor.ConstructQuery(tableMetadataObject)
        insertQuery.setInsert(addedValues)

    # form DELETE query

    deleteID = request.args.get(constants.deleteIDName)
    if deleteID is not None:
        deleteQuery = queryconstructor.ConstructQuery(tableMetadataObject)
        deleteQuery.setDelete(deleteID)

    # run queries

    try:
        if ('insertQuery' in locals()): cur.execute(insertQuery.query, insertQuery.args)
        if ('deleteQuery' in locals()): cur.execute(deleteQuery.query, deleteQuery.args)
        cur.execute(selectQuery.query, selectQuery.args)
        globalvars.tableData = cur.fetchall()
    except:
        return render_template("tableView.html", tableName=tableName,
                               tablePickerElements=dbconnector.scheduleDB.tablesList,
                               columnPickerElements=selectQuery.currentColumns,
                               selectedColumns=searchColumn,
                               selectedConditions=conditions, selectedLogicalConnections=logicalConnections,
                               selectedOrder=orderColumn, selectedStrings=searchString,
                               selectedPagination=rowsOnPageNumber, selectedPage=selectedPage, incorrectQuery=1)

    return render_template("tableView.html", tableName=tableName, tablePickerElements=dbconnector.scheduleDB.tablesList,
                           columnPickerElements=selectQuery.currentColumns,
                           selectedColumns=searchColumn,
                           selectedConditions=conditions, selectedLogicalConnections=logicalConnections,
                           selectedOrder=orderColumn, selectedStrings=searchString,
                           selectedPagination=rowsOnPageNumber, selectedPage=selectedPage,
                           columnNames=columnNames, tableData=globalvars.tableData, meta=tableMetadataDict,
                           tableColumns=[x for x in columnNames if tableMetadataDict[x].type != 'key'])


@app.route("/rowEdit", methods=['GET', 'POST'])
def rowEdit():
    tableName = request.args.get('tableName')
    editID = request.args.get('editID')
    columnNames = request.args.getlist('columnNames')
    fullColumnNames = columnNames.copy()
    tableMetadataObject = getattr(metadata, tableName.lower())
    tableMetadataDict = tableMetadataObject.get_meta()

    for i in range(len(columnNames)):
        if (columnNames[i] == 'ID'):
            idColumn = i;

    for i in range(len(globalvars.tableData)):
        if (str(globalvars.tableData[i][idColumn]) == str(editID)):
            editRow = i;

    editRow = list(globalvars.tableDataWithoutRef[editRow])

    for i in range(len(fullColumnNames)):
        if (tableMetadataDict[fullColumnNames[i]].type == 'key'):
            editRow.pop(i)
            columnNames.pop(i)

    return render_template('rowEdit.html', columnNames=columnNames, columns=editRow, rowID=editID, tableName=tableName,
                           fullColumnNames=fullColumnNames)


@app.route("/editInTable", methods=['GET', 'POST'])
def editInTable():
    tableName = request.args.get('tableName')
    columns = request.args.getlist('columns')[0]
    columns = columns.replace('[', '').replace(']', '').replace("'", '').replace("\"", '').replace(",", '|').split('|')
    fullColumnNames = request.args.getlist('fullColumnNames')[0].replace('[', '').replace(']', '').replace("'",'').replace("\"", '').replace(",", '|').split('|')
    fullColumnNames = [i.strip() for i in fullColumnNames]
    rowID = request.args.get('rowID')
    columnNames = request.args.getlist('columnNames')[0].replace('[', '').replace(']', '').replace("'", '').replace("\"", '').replace(",", '').split()
    newColumns = request.args.getlist(constants.editInputName)

    dbconnector.scheduleDB.connect_to_database()
    dbconnector.scheduleDB.set_tables_list()
    cur = dbconnector.scheduleDB.cur
    tableMetadataObject = getattr(metadata, tableName.lower())
    tableMetadataDict = tableMetadataObject.get_meta()
    oldRow = list(cur.execute("SELECT * FROM %s WHERE ID = (?)" % tableName, [rowID]).fetchall()[0])
    for i in range(len(oldRow)):
        if (tableMetadataDict[fullColumnNames[i]].type == 'key'):
            oldRow.pop(i)

    for i in range(len(oldRow)):
        if (str(oldRow[i]).strip() != str(columns[i]).strip()):
            return render_template('updateResult.html', mode='outdated')

    query = queryconstructor.ConstructQuery(tableMetadataObject)
    query.setUpdate(newColumns, columnNames, rowID)
    cur.execute(query.query)
    return render_template('updateResult.html', mode='success')


if __name__ == "__main__":
    app.run(debug=True)
