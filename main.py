import metadata
import queryconstructor
import dbconnector
from flask import Flask, url_for, render_template, request
from flask_jsglue import JSGlue


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
    hideCellsCheckboxName = 'hideCells'
    visibleColumnsPickerName = 'visibleColumnsPicker'
    defaultXOrderID = 4
    defaultYOrderID = 7


class GlobalVars:
    tableData = []
    tableDataWithoutRef = []
    cur = None


constants = Constants()
globalvars = GlobalVars()


def create_app():
    app = Flask(__name__)
    jsglue = JSGlue(app)

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


class ScheduleCommon():
    def executeCommonCode(self):
        self.searchColumn = request.args.getlist(constants.columnPickerName)
        self.searchString = request.args.getlist(constants.inputName)
        self.conditions = request.args.getlist(constants.conditionsPickerName)
        self.logicalConnections = ['WHERE'] + request.args.getlist(constants.logicalConnectionName)
        self.columnNames = globalvars.cur.execute(dbconnector.GETCOLUMNNAMES % (self.tableName)).fetchall()
        self.columnNames = [str(i[0]).strip() for i in self.columnNames]
        self.tableMetadataObject = getattr(metadata, self.tableName.lower())
        self.tableMetadataDict = self.tableMetadataObject.get_meta()

        self.selectQuery = queryconstructor.ConstructQuery(self.tableMetadataObject)
        self.selectQuery.setSelect()
        globalvars.tableDataWithoutRef = globalvars.cur.execute(self.selectQuery.query).fetchall()
        for i in self.columnNames:
            if self.tableMetadataDict[i].type == 'ref':
                self.selectQuery.replaceField(self.tableMetadataDict[i].refTable, i, self.tableMetadataDict[i].refKey,
                                              self.tableMetadataDict[i].refName)
        for i in range(len(self.searchString)):
            self.selectQuery.search(self.searchColumn[i], self.searchString[i], self.conditions[i],
                                    self.logicalConnections[i])

    def initTableView(self):
        self.tableName = request.args.get(constants.tablePickerName)
        if (self.tableName is None):
            self.tableName = dbconnector.scheduleDB.tablesList[0]
        self.orderColumn = request.args.get(constants.orderPickerName)
        self.rowsOnPageNumber = request.args.get(constants.paginationPickerName)
        if self.rowsOnPageNumber is None:
            self.rowsOnPageNumber = constants.paginationPickerElements[0]
        self.selectedPage = request.args.get(constants.pagePickerName)
        if self.selectedPage is None:
            self.selectedPage = 0
        self.executeCommonCode()
        self.selectQuery.order(self.orderColumn)


@app.route("/", methods=['GET', 'POST'])
def view_table():
    sc = ScheduleCommon()
    sc.initTableView()

    # form INSERT query

    addedValues = request.args.getlist(constants.addIntoTableInputsName)
    if (len(addedValues) > 0 and len(addedValues[0]) > 0):
        insertQuery = queryconstructor.ConstructQuery(sc.tableMetadataObject)
        insertQuery.setInsert(addedValues)

    # form DELETE query

    deleteID = request.args.get(constants.deleteIDName)
    if deleteID is not None:
        deleteQuery = queryconstructor.ConstructQuery(sc.tableMetadataObject)
        deleteQuery.setDelete(deleteID)

    # run queries

    try:
        if ('insertQuery' in locals()): globalvars.cur.execute(insertQuery.query, insertQuery.args)
        if ('deleteQuery' in locals()): globalvars.cur.execute(deleteQuery.query, deleteQuery.args)
        print(sc.selectQuery.query, sc.selectQuery.args)
        globalvars.cur.execute(sc.selectQuery.query, sc.selectQuery.args)
        globalvars.tableData = globalvars.cur.fetchall()
    except:
        return render_template("tableView.html", tableName=sc.tableName,
                               tablePickerElements=dbconnector.scheduleDB.tablesList,
                               columnPickerElements=sc.selectQuery.currentColumns,
                               selectedColumns=sc.searchColumn,
                               selectedConditions=sc.conditions, selectedLogicalConnections=sc.logicalConnections,
                               selectedOrder=sc.orderColumn, selectedStrings=sc.searchString,
                               selectedPagination=sc.rowsOnPageNumber, selectedPage=sc.selectedPage, incorrectQuery=1)

    return render_template("tableView.html", tableName=sc.tableName,
                           tablePickerElements=dbconnector.scheduleDB.tablesList,
                           columnPickerElements=sc.selectQuery.currentColumns,
                           selectedColumns=sc.searchColumn,
                           selectedConditions=sc.conditions, selectedLogicalConnections=sc.logicalConnections,
                           selectedOrder=sc.orderColumn, selectedStrings=sc.searchString,
                           selectedPagination=sc.rowsOnPageNumber, selectedPage=sc.selectedPage,
                           columnNames=sc.columnNames, tableData=globalvars.tableData, meta=sc.tableMetadataDict,
                           tableColumns=[x for x in sc.columnNames if sc.tableMetadataDict[x].type != 'key'])


@app.route("/rowEdit", methods=['GET', 'POST'])
def rowEdit():
    tableName = request.args.get('tableName')
    editID = request.args.get('editID')

    tableMetadataObject = getattr(metadata, tableName.lower())
    tableMetadataDict = tableMetadataObject.get_meta()
    columnNames = tableMetadataObject.get_fields()
    columnMetaNames = [tableMetadataDict[i].name for i in columnNames]

    query = queryconstructor.ConstructQuery(tableMetadataObject)
    query.setSelect()
    query.search('ID',editID,'=','where')
    editRow = list(globalvars.cur.execute(query.query,query.args).fetchall()[0])

    if 'xColumnValue' in request.args.keys():
        xColumnValue = request.args.get('xColumnValue')
        yColumnValue = request.args.get('yColumnValue')
        for i in editRow:
            pass

    fullColumnNames = columnNames.copy()
    for i in range(len(fullColumnNames)):
        if (tableMetadataDict[fullColumnNames[i]].type == 'key'):
            editRow.pop(i)
            columnNames.pop(i)
            columnMetaNames.pop(i)

    return render_template('rowEdit.html', columnNames=columnNames, columnMetaNames = columnMetaNames, columns=editRow, rowID=editID, tableName=tableName)


@app.route("/editInTable", methods=['GET', 'POST'])
def editInTable():
    tableName = request.args.get('tableName')
    tableMetadataObject = getattr(metadata, tableName.lower())
    tableMetadataDict = tableMetadataObject.get_meta()
    fullColumnNames = tableMetadataObject.get_fields()
    newColumns = request.args.getlist(constants.editInputName)

    columnsDataBeforeEdit = request.args.getlist('columns')[0]
    columnsDataBeforeEdit = columnsDataBeforeEdit.replace('[', '').replace(']', '').replace("'", '').replace("\"", '').replace(",", '|').split('|')
    rowID = request.args.get('rowID')
    columnNames = fullColumnNames.copy()
    for i in range(len(fullColumnNames)):
        if (tableMetadataDict[fullColumnNames[i]].type == 'key'):
            columnNames.pop(i)


    columnsDataNow = list(globalvars.cur.execute("SELECT * FROM %s WHERE ID = (?)" % tableName, [rowID]).fetchall()[0])
    for i in range(len(columnsDataNow)):
        if (tableMetadataDict[fullColumnNames[i]].type == 'key'):
            columnsDataNow.pop(i)

    for i in range(len(columnsDataNow)):
        if (str(columnsDataNow[i]).strip() != str(columnsDataBeforeEdit[i]).strip()):
            return render_template('updateResult.html', mode='outdated')

    query = queryconstructor.ConstructQuery(tableMetadataObject)
    query.setUpdate(newColumns, columnNames, rowID)
    try:
        globalvars.cur.execute(query.query, query.args)
    except:
        return render_template('updateResult.html', mode='incorrect')
    return render_template('updateResult.html', mode='success')


@app.route("/schedule", methods=['GET', 'POST'])
def viewSchedule():
    sc = ScheduleCommon()
    sc.tableName = constants.schedItemsTableName

    sc.executeCommonCode()

    globalvars.cur.execute(sc.selectQuery.query, sc.selectQuery.args)
    tableData = globalvars.cur.fetchall()
    tableData = [list(i) for i in tableData]

    hideHeaders = request.args.get(constants.hideHeadersCheckboxName)
    if (hideHeaders is None):
        hideHeaders = 0

    hideCells = request.args.get(constants.hideCellsCheckboxName)
    if (hideCells is None):
        hideCells = 0

    xOrderName = request.args.get(constants.xGroupingPickerName)
    yOrderName = request.args.get(constants.yGroupingPickerName)
    if (xOrderName is None):
        xOrderID = constants.defaultXOrderID
    else:
        xOrderID = [i.name for i in sc.tableMetadataDict.values()].index(xOrderName)

    if (yOrderName is None):
        yOrderID = constants.defaultYOrderID
    else:
        yOrderID = [i.name for i in sc.tableMetadataDict.values()].index(yOrderName)


    for i in tableData:
        for j in range(len(i)):
            if sc.tableMetadataDict[sc.columnNames[j]].type == 'key':
                i.append(i[j])

    xName = sc.tableMetadataDict[sc.columnNames[xOrderID]].name
    yName = sc.tableMetadataDict[sc.columnNames[yOrderID]].name
    xColumnName = sc.columnNames[xOrderID]
    yColumnName = sc.columnNames[yOrderID]
    t1, t2 = sc.columnNames[xOrderID], sc.columnNames[yOrderID]
    sc.columnNames.remove(t1)
    if (t1 != t2): sc.columnNames.remove(t2)

    scheduleTable = dict.fromkeys(i[yOrderID] for i in tableData)
    for key in scheduleTable:
        scheduleTable[key] = dict.fromkeys([i[xOrderID] for i in tableData])

    visibleColumns = request.args.getlist(constants.visibleColumnsPickerName)
    if (visibleColumns is None) or (len(visibleColumns) == 0):
        visibleColumns = [i.name for i in sc.tableMetadataDict.values()]
    visibleColumnNames = []
    visibleColumnNumbers = []
    for i in range(len(sc.columnNames)):
        if (sc.tableMetadataDict[sc.columnNames[i]].name in visibleColumns):
            visibleColumnNames.append(sc.columnNames[i])
            visibleColumnNumbers.append(i)

    for i in tableData:
        t = i.copy()
        del t[max(xOrderID, yOrderID)]
        if (xOrderID != yOrderID): del t[min(xOrderID, yOrderID)]
        if scheduleTable[i[yOrderID]][i[xOrderID]] is None:
            scheduleTable[i[yOrderID]][i[xOrderID]] = [t]
        else:
            scheduleTable[i[yOrderID]][i[xOrderID]].append(t)
    return render_template('scheduleView.html', tableData=scheduleTable, meta=sc.tableMetadataDict,
                           columnNames=sc.columnNames, xName=xName, yName=yName, xColumnName=xColumnName, yColumnName=yColumnName,
                           pickerElements=[i.name for i in sc.tableMetadataDict.values()], hideHeaders=hideHeaders, hideCells = hideCells,
                           columnPickerElements=sc.selectQuery.currentColumns, selectedColumns=sc.searchColumn,
                           selectedConditions=sc.conditions, selectedLogicalConnections=sc.logicalConnections,
                           selectedStrings=sc.searchString, visibleColumnNames=visibleColumnNames,
                           visibleColumnNumbers=visibleColumnNumbers, tableName = sc.tableName)


if __name__ == "__main__":
    app.run(debug=True)
