import sys

import metadata
import queryconstructor
import dbconnector
import conflicts
from flask import Flask, url_for, render_template, request, redirect
from flask_jsglue import JSGlue
from collections import OrderedDict

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
    conflictsSearcher = None

constants = Constants()
globalvars = GlobalVars()


def create_app():
    app = Flask(__name__)
    jsglue = JSGlue(app)

    def run_on_start():
        dbconnector.scheduleDB.connect_to_database()
        dbconnector.scheduleDB.set_tables_list()
        globalvars.cur = dbconnector.scheduleDB.cur
        globalvars.conflictsSearcher = conflicts.ConflictsSearcher(globalvars.cur)

    run_on_start()
    return app


app = create_app()


@app.context_processor
def inject_globals():
    return constants.get_constants()


class dataWorker():

    def setDefaultTableName(self):
        self.tableName = dbconnector.scheduleDB.tablesList[0]

    def init(self):
        self.columnNames = globalvars.cur.execute(dbconnector.GETCOLUMNNAMES % (self.tableName)).fetchall()
        self.columnNames = [str(i[0]).strip() for i in self.columnNames]
        self.tableMetadataObject = getattr(metadata, self.tableName.lower())
        self.tableMetadataDict = self.tableMetadataObject.get_meta()

    def getSearchBarData(self):
        self.init()
        self.searchColumn = request.args.getlist(constants.columnPickerName)
        self.searchString = request.args.getlist(constants.inputName)
        self.conditions = request.args.getlist(constants.conditionsPickerName)
        self.logicalConnections = ['WHERE'] + request.args.getlist(constants.logicalConnectionName)

    def getOrderAndPaginationBarData(self):
        self.orderColumn = request.args.get(constants.orderPickerName)
        if (self.orderColumn is None):
            self.orderColumn = self.columnNames[0]
        self.rowsOnPageNumber = request.args.get(constants.paginationPickerName)
        if self.rowsOnPageNumber is None:
            self.rowsOnPageNumber = constants.paginationPickerElements[0]
        self.selectedPage = request.args.get(constants.pagePickerName)
        if self.selectedPage is None:
            self.selectedPage = 0

    def getDataForViewSchedule(self):
        self.tableName = constants.schedItemsTableName
        self.init()
        self.getSearchBarData()
        if constants.hideHeadersCheckboxName in request.args:
            self.hideHeaders = request.args.get(constants.hideHeadersCheckboxName)
        else:
            self.hideHeaders = 0

        if constants.hideCellsCheckboxName in request.args:
            self.hideCells = request.args.get(constants.hideCellsCheckboxName)
        else:
            self.hideCells = 0

        if constants.xGroupingPickerName in request.args:
            xOrderName = request.args.get(constants.xGroupingPickerName)
            self.xOrderID = [i.name for i in self.tableMetadataDict.values()].index(xOrderName)
        else:
            self.xOrderID = constants.defaultXOrderID

        if constants.yGroupingPickerName in request.args:
            yOrderName = request.args.get(constants.yGroupingPickerName)
            self.yOrderID = [i.name for i in self.tableMetadataDict.values()].index(yOrderName)
        else:
            self.yOrderID = constants.defaultYOrderID

    def getDataForViewTable(self):
        if (constants.tablePickerName) in request.args:
            self.tableName = request.args.get(constants.tablePickerName)
        else:
            self.setDefaultTableName()
        self.init()
        self.getSearchBarData()
        self.getOrderAndPaginationBarData()

    def formSelectQuery(self):
        self.selectQuery = queryconstructor.ConstructQuery(self.tableMetadataObject)
        self.selectQuery.setSelect()
        globalvars.tableDataWithoutRef = globalvars.cur.execute(self.selectQuery.query).fetchall()
        for i in self.columnNames:
            if self.tableMetadataDict[i].type == 'ref':
                self.selectQuery.replaceField(self.tableMetadataDict[i].refTable, i, self.tableMetadataDict[i].refKey,
                                              self.tableMetadataDict[i].refName)
        if ('searchString') in locals():
            for i in range(len(self.searchString)):
                self.selectQuery.search(self.searchColumn[i], self.searchString[i], self.conditions[i],
                                        self.logicalConnections[i])
        if ('orderColumn') in locals(): self.selectQuery.order(self.orderColumn)

    def formInsertQuery(self):
        addedValues = request.args.getlist(constants.addIntoTableInputsName)
        if len(addedValues) > 0 and len(addedValues[0]) > 0:
            self.insertQuery = queryconstructor.ConstructQuery(self.tableMetadataObject)
            self.insertQuery.setInsert(addedValues)
            return True
        else:
            return False

    def formDeleteQuery(self):
        if (constants.deleteIDName in request.args):
            deleteID = request.args.get(constants.deleteIDName)
            self.deleteQuery = queryconstructor.ConstructQuery(self.tableMetadataObject)
            self.deleteQuery.setDelete(deleteID)
            return True
        else:
            return False


@app.route("/", methods=['GET', 'POST'])
def view_table():
    dw = dataWorker()
    dw.getDataForViewTable()
    dw.formSelectQuery()

    try:
        if (dw.formInsertQuery()):
            globalvars.cur.execute(dw.insertQuery.query, dw.insertQuery.args)
            globalvars.conflictsSearcher.setOutdated()
        if (dw.formDeleteQuery()):
            globalvars.cur.execute(dw.deleteQuery.query, dw.deleteQuery.args)
            globalvars.conflictsSearcher.setOutdated()
        globalvars.cur.execute(dw.selectQuery.query, dw.selectQuery.args)
        globalvars.tableData = globalvars.cur.fetchall()
        incorrectQuery = 0
    except:
        incorrectQuery = 1
    return render_template("tableView.html", tableName=dw.tableName,
                           tablePickerElements=dbconnector.scheduleDB.tablesList,
                           columnPickerElements=dw.selectQuery.currentColumns,
                           selectedColumns=dw.searchColumn,
                           selectedConditions=dw.conditions, selectedLogicalConnections=dw.logicalConnections,
                           selectedOrder=dw.orderColumn, selectedStrings=dw.searchString,
                           selectedPagination=dw.rowsOnPageNumber, selectedPage=dw.selectedPage,
                           columnNames=dw.columnNames, tableData=globalvars.tableData, meta=dw.tableMetadataDict,
                           tableColumns=[x for x in dw.columnNames if dw.tableMetadataDict[x].type != 'key'],
                           incorrectQuery=incorrectQuery)

@app.route("/rowEdit", methods=['GET', 'POST'])
def rowEdit():

    tableName = request.args.get('tableName')
    editID = request.args.get('editID')

    tableMetadataObject = getattr(metadata, tableName.lower())
    tableMetadataDict = tableMetadataObject.get_meta()
    columnNames = tableMetadataObject.get_fields()
    columnMetaNames = [tableMetadataDict[i].name for i in columnNames]
    addVals = request.args.get('addVals')
    dNg = request.args.get('dNg')
    returnURL = request.args.get('returnURL')

    query = queryconstructor.ConstructQuery(tableMetadataObject)
    query.setSelect()
    queries = []
    qieriesIDS = []
    for i in columnNames:
        if tableMetadataDict[i].type == 'ref':
            tq = "SELECT %s from %s" % (tableMetadataDict[i].refName,tableMetadataDict[i].refTable)
            tr = globalvars.cur.execute(tq).fetchall()
            tr = [i[0] for i in tr]
            queries.append(tr)
            tq = "SELECT %s from %s" % (tableMetadataDict[i].refKey, tableMetadataDict[i].refTable)
            tr = globalvars.cur.execute(tq).fetchall()
            tr = [i[0] for i in tr]
            qieriesIDS.append(tr)
    query.search(tableName+'.ID', editID, '=', 'where')
    editRow = list(globalvars.cur.execute(query.query,query.args).fetchall()[0])
    selectedVals = editRow.copy()
    cnt = 0
    for i in range(len(columnNames)):
        if tableMetadataDict[columnNames[i]].type == 'ref':
            editRow[i] = queries[cnt]
            cnt += 1

    fullColumnNames = columnNames.copy()
    for i in range(len(fullColumnNames)):
        if (tableMetadataDict[fullColumnNames[i]].type == 'key'):
            editRow.pop(i)
            columnNames.pop(i)
            columnMetaNames.pop(i)
            selectedVals.pop(i)

    editRow = [i + [None] if isinstance(i,list) else i for i in editRow]
    qieriesIDS = [i+[None] for i in qieriesIDS]

    oldRowData = selectedVals.copy()
    if 'xColumnValue' in request.args.keys():
        xColumnValue = request.args.get('xColumnValue')
        yColumnValue = request.args.get('yColumnValue')
        xColumnName = request.args.getlist('xColumnName')[0]
        yColumnName = request.args.getlist('yColumnName')[0]
        if (xColumnValue != 'None'):
            selectedVals[columnNames.index(xColumnName)] = queries[columnNames.index(xColumnName)].index(xColumnValue) + 1
        else:
            selectedVals[columnNames.index(xColumnName)] = None
        if (yColumnValue != 'None'):
            selectedVals[columnNames.index(yColumnName)] = queries[columnNames.index(yColumnName)].index(yColumnValue) + 1
        else:
            selectedVals[columnNames.index(yColumnName)] = None

    return render_template('rowEdit.html', columnNames=columnNames, columnMetaNames = columnMetaNames, columns=editRow, rowID=editID, tableName=tableName, qieriesIDS = qieriesIDS,selectedVals=selectedVals, oldRowData = oldRowData,addVals=addVals,dNg=dNg,returnURL=returnURL)


@app.route("/editInTable", methods=['GET', 'POST'])
def editInTable():
    dw = dataWorker()
    dw.tableName = request.args.get('tableName')
    dw.init()
    dw.fullColumnNames = dw.tableMetadataObject.get_fields()
    newColumns = request.args.getlist(constants.editInputName)
    newColumns = [i if i != 'None' else None for i in newColumns]
    if (dw.formInsertQuery()):
        globalvars.cur.execute(dw.insertQuery.query, dw.insertQuery.args)
        globalvars.conflictsSearcher.setOutdated()
        return redirect(url_for('view_table', tablesPicker=dw.tableName))

    columnsDataBeforeEdit = request.args.getlist('columns')[0]
    columnsDataBeforeEdit = columnsDataBeforeEdit.replace('[', '').replace(']', '').replace("'", '').replace("\"", '').replace(",", '|').split('|')
    rowID = request.args.get('rowID')
    columnNames = dw.fullColumnNames.copy()
    for i in range(len(dw.fullColumnNames)):
        if (dw.tableMetadataDict[dw.fullColumnNames[i]].type == 'key'):
            columnNames.pop(i)


    columnsDataNow = list(globalvars.cur.execute("SELECT * FROM %s WHERE ID = (?)" % dw.tableName, [rowID]).fetchall()[0])
    for i in range(len(columnsDataNow)):
        if (dw.tableMetadataDict[dw.fullColumnNames[i]].type == 'key'):
            columnsDataNow.pop(i)

    for i in range(len(columnsDataNow)):
        if (str(columnsDataNow[i]).strip() != str(columnsDataBeforeEdit[i]).strip()):
            return render_template('updateResult.html', mode='outdated')

    query = queryconstructor.ConstructQuery(dw.tableMetadataObject)
    query.setUpdate(newColumns, columnNames, rowID)
    try:
        globalvars.cur.execute(query.query, query.args)
        globalvars.conflictsSearcher.setOutdated()
    except:
        return render_template('updateResult.html', mode='incorrect')
    returnURL = request.args.get('returnURL')
    if (returnURL is not None and returnURL != 'None'):
        return redirect(returnURL)
    return redirect(url_for('view_table',tablesPicker=dw.tableName))


@app.route("/schedule", methods=['GET', 'POST'])
def viewSchedule():
    dw = dataWorker()
    dw.getDataForViewSchedule()
    dw.formSelectQuery()
    xName = dw.tableMetadataDict[dw.columnNames[dw.xOrderID]].name
    yName = dw.tableMetadataDict[dw.columnNames[dw.yOrderID]].name
    xColumnName = dw.columnNames[dw.xOrderID]
    yColumnName = dw.columnNames[dw.yOrderID]
    dw.selectQuery.order(yColumnName)
    globalvars.cur.execute(dw.selectQuery.query, dw.selectQuery.args)
    tableData = globalvars.cur.fetchall()
    tableData = [list(i) for i in tableData]

    for i in tableData:
        for j in range(len(i)):
            if dw.tableMetadataDict[dw.columnNames[j]].type == 'key':
                i.append(i[j])

    t1, t2 = dw.columnNames[dw.xOrderID], dw.columnNames[dw.yOrderID]
    dw.columnNames.remove(t1)
    if (t1 != t2): dw.columnNames.remove(t2)

    scheduleTable = OrderedDict.fromkeys(i[dw.yOrderID] for i in tableData)
    for key in scheduleTable:
        scheduleTable[key] = dict.fromkeys([i[dw.xOrderID] for i in sorted(tableData,key = lambda x: x[dw.xOrderID] if x[dw.xOrderID] is not None else chr(sys.maxunicode))])

    visibleColumns = request.args.getlist(constants.visibleColumnsPickerName)
    if (visibleColumns is None) or (len(visibleColumns) == 0):
        visibleColumns = [i.name for i in dw.tableMetadataDict.values()]
    visibleColumnNames = []
    visibleColumnNumbers = []
    for i in range(len(dw.columnNames)):
        if (dw.tableMetadataDict[dw.columnNames[i]].name in visibleColumns):
            visibleColumnNames.append(dw.columnNames[i])
            visibleColumnNumbers.append(i)

    for i in tableData:
        t = i.copy()
        del t[max(dw.xOrderID, dw.yOrderID)]
        if (dw.xOrderID != dw.yOrderID): del t[min(dw.xOrderID, dw.yOrderID)]
        if scheduleTable[i[dw.yOrderID]][i[dw.xOrderID]] is None:
            scheduleTable[i[dw.yOrderID]][i[dw.xOrderID]] = [t]
        else:
            scheduleTable[i[dw.yOrderID]][i[dw.xOrderID]].append(t)

    return render_template('scheduleView.html', tableData=scheduleTable, meta=dw.tableMetadataDict,
                           columnNames=dw.columnNames, xName=xName, yName=yName, xColumnName=xColumnName, yColumnName=yColumnName,
                           pickerElements=[i.name for i in dw.tableMetadataDict.values()], hideHeaders=dw.hideHeaders, hideCells = dw.hideCells,
                           columnPickerElements=dw.selectQuery.currentColumns, selectedColumns=dw.searchColumn,
                           selectedConditions=dw.conditions, selectedLogicalConnections=dw.logicalConnections,
                           selectedStrings=dw.searchString, visibleColumnNames=visibleColumnNames,
                           visibleColumnNumbers=visibleColumnNumbers, tableName = dw.tableName)


@app.route("/conflicts", methods=['GET', 'POST'])
def viewConflicts():
    dw = dataWorker()
    dw.tableName = constants.schedItemsTableName
    dw.init()
    dw.formSelectQuery()
    tQueryR = dw.selectQuery.query.replace("Sched_Items","r")
    queryPartsR = tQueryR.replace('from','SELECT').split("SELECT")
    tQueryL = dw.selectQuery.query.replace("Sched_Items","l")
    queryPartsL = tQueryL.replace('from','SELECT').split("SELECT")
    globalvars.conflictsSearcher.setSelectedColumns(queryPartsR[1],queryPartsR[2][2:],queryPartsL[1],queryPartsL[2][2:])
    globalvars.conflictsSearcher.findConflicts()

    return (render_template("conflictsView.html",conflictsByTypes = globalvars.conflictsSearcher.conflictsByTypes, columnNames = dw.columnNames, meta=dw.tableMetadataDict, selectedPage = 0, selectedPagination = 100))

if __name__ == "__main__":
    app.run(debug=True)
