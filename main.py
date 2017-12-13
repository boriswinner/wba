import metadata
import queryconstructor
import dbconnector
from flask import Flask, url_for, render_template, request


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
    schedItemsTableName = 'SCHED_ITEMS'
    xGroupingPickerName = 'xGroupingPicker'
    yGroupingPickerName = 'yGroupingPicker'
    hideHeadersCheckboxName = 'hideHeaders'
    visibleColumnsPickerName = 'visibleColumnsPicker'


class GlobalVars:
    tableData = []
    tableDataWithoutRef = []
    cur = None


constants = Constants()
globalvars = GlobalVars()


def create_app():
    app = Flask(__name__)

    def run_on_start():
        dbconnector.scheduleDB.connect_to_database()
        dbconnector.scheduleDB.set_tables_list()
        globalvars.cur = dbconnector.scheduleDB.cur

    run_on_start()
    return app


app = create_app()


@app.context_processor
def inject_globals():
    return constants.get_constants()


@app.route("/", methods=['GET', 'POST'])
def view_table():
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
    columnNames = globalvars.cur.execute(dbconnector.GETCOLUMNNAMES % (tableName)).fetchall()
    columnNames = [str(i[0]).strip() for i in columnNames]
    selectedPage = request.args.get(constants.pagePickerName)
    if selectedPage is None:
        selectedPage = 0

    # form SELECT query

    tableMetadataObject = getattr(metadata, tableName.lower())
    tableMetadataDict = tableMetadataObject.get_meta()
    selectQuery = queryconstructor.ConstructQuery(tableMetadataObject)
    selectQuery.setSelect()
    globalvars.tableDataWithoutRef = globalvars.cur.execute(selectQuery.query).fetchall()
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
        if ('insertQuery' in locals()): globalvars.cur.execute(insertQuery.query, insertQuery.args)
        if ('deleteQuery' in locals()): globalvars.cur.execute(deleteQuery.query, deleteQuery.args)
        globalvars.cur.execute(selectQuery.query, selectQuery.args)
        globalvars.tableData = globalvars.cur.fetchall()
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
            idColumn = i

    for i in range(len(globalvars.tableData)):
        if (str(globalvars.tableData[i][idColumn]) == str(editID)):
            editRow = i

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
    fullColumnNames = request.args.getlist('fullColumnNames')[0].replace('[', '').replace(']', '').replace("'",
                                                                                                           '').replace(
        "\"", '').replace(",", '|').split('|')
    fullColumnNames = [i.strip() for i in fullColumnNames]
    rowID = request.args.get('rowID')
    columnNames = request.args.getlist('columnNames')[0].replace('[', '').replace(']', '').replace("'", '').replace(
        "\"", '').replace(",", '').split()
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


@app.route("/schedule", methods=['GET', 'POST'])
def viewSchedule():
    tableName = constants.schedItemsTableName

    #copypaste
    searchColumn = request.args.getlist(constants.columnPickerName)
    searchString = request.args.getlist(constants.inputName)
    conditions = request.args.getlist(constants.conditionsPickerName)
    logicalConnections = ['WHERE'] + request.args.getlist(constants.logicalConnectionName)
    columnNames = globalvars.cur.execute(dbconnector.GETCOLUMNNAMES % (tableName)).fetchall()
    columnNames = [str(i[0]).strip() for i in columnNames]

    visibleColumns = request.args.getlist(constants.visibleColumnsPickerName)
    print(visibleColumns)
    #return str(visibleColumns)

    tableMetadataObject = getattr(metadata, tableName.lower())
    tableMetadataDict = tableMetadataObject.get_meta()

    selectQuery = queryconstructor.ConstructQuery(tableMetadataObject)
    selectQuery.setSelect()
    for i in columnNames:
        if tableMetadataDict[i].type == 'ref':
            selectQuery.replaceField(tableMetadataDict[i].refTable, i, tableMetadataDict[i].refKey,
                                     tableMetadataDict[i].refName)
    selectQuery.setVisible(visibleColumns)
    for i in range(len(searchString)):
        selectQuery.search(searchColumn[i], searchString[i], conditions[i], logicalConnections[i])

    print(selectQuery.query)
    globalvars.cur.execute(selectQuery.query,selectQuery.args)
    tableData = globalvars.cur.fetchall()  # not sure if global needed
    tableData = [list(i) for i in tableData]

    hideHeaders = request.args.get(constants.hideHeadersCheckboxName)
    if (hideHeaders is None):
        hideHeaders = 0

    xOrderName = request.args.get(constants.xGroupingPickerName)
    yOrderName = request.args.get(constants.yGroupingPickerName)
    if (xOrderName is None):
        xOrderID = 0  # temporary magic numbers
    else:
        xOrderID = [i.name for i in tableMetadataDict.values()].index(xOrderName)

    if (yOrderName is None):
        yOrderID = 0  # temporary magic numbers
    else:
        yOrderID = [i.name for i in tableMetadataDict.values()].index(yOrderName)
    xName = tableMetadataDict[columnNames[xOrderID]].name
    yName = tableMetadataDict[columnNames[yOrderID]].name
    t1, t2 = columnNames[xOrderID], columnNames[yOrderID]
    columnNames.remove(t1)
    if (t1 != t2): columnNames.remove(t2)

    scheduleTable = dict.fromkeys(i[yOrderID] for i in tableData)
    for key in scheduleTable:
        scheduleTable[key] = dict.fromkeys([i[xOrderID] for i in tableData])

    for i in tableData:
        t = i.copy()
        del t[max(xOrderID, yOrderID)]
        if (xOrderID != yOrderID): del t[min(xOrderID, yOrderID)]
        if scheduleTable[i[yOrderID]][i[xOrderID]] is None:
            scheduleTable[i[yOrderID]][i[xOrderID]] = [t]
        else:
            scheduleTable[i[yOrderID]][i[xOrderID]].append(t)

    return render_template('scheduleView.html', tableData=scheduleTable, meta=tableMetadataDict, selectedPage=0,
                           selectedPagination=100, columnNames=columnNames, xName = xName, yName = yName, pickerElements =[i.name for i in tableMetadataDict.values()], hideHeaders = hideHeaders, columnPickerElements=selectQuery.currentColumns, selectedColumns=searchColumn,
                           selectedConditions=conditions, selectedLogicalConnections=logicalConnections, selectedStrings=searchString)

if __name__ == "__main__":
    app.run(debug=True)
