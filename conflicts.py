import dbconnector

#constants
sameGroupDifferentLessonQuery = """SELECT %s, %s FROM SCHED_ITEMS r CROSS JOIN SCHED_ITEMS l %s %s WHERE 
r.LESSON_ID = l.LESSON_ID AND r.GROUP_ID = l.GROUP_ID AND r.WEEKDAY_ID = l.WEEKDAY_ID 
AND (r.AUDIENCE_ID != l.AUDIENCE_ID OR r.TEACHER_ID != l.TEACHER_ID OR r.TYPE_ID != l.TYPE_ID OR r.SUBJECT_ID != l.SUBJECT_ID) """

differentGroupsSameLessonQuery = """SELECT %s, %s FROM SCHED_ITEMS r CROSS JOIN SCHED_ITEMS l %s %s WHERE 
r.LESSON_ID = l.LESSON_ID AND r.GROUP_ID != l.GROUP_ID AND r.WEEKDAY_ID = l.WEEKDAY_ID 
AND (r.AUDIENCE_ID = l.AUDIENCE_ID OR r.TEACHER_ID = l.TEACHER_ID) """

class ConflictType():
    def __init__(self,query, name):
        self.query = query
        self.label = name
        self.data = None


class ConflictsSearcher():
    def __init__(self, cur):
        self.cur = cur
        self.isUpdated = False
        self.columnNames = cur.execute(dbconnector.GETCOLUMNNAMES % ("SCHED_ITEMS")).fetchall()
        self.columnNames = [str(i[0]).strip() for i in self.columnNames] * 2
        self.IDposition = self.columnNames.index("ID")

    def setSelectedColumns(self,selectedColumnsR, tablesToJoinR, selectedColumnsL, tablesToJoinL):
        self.selectedColumnsR = selectedColumnsR
        self.tablesToJoinR = tablesToJoinR
        self.selectedColumnsL = selectedColumnsL
        self.tablesToJoinL = tablesToJoinL

    def setOutdated(self):
        self.isUpdated = False

    conflictsByTypes = [
        ConflictType(sameGroupDifferentLessonQuery,"The same group has different lessons simultaneously"),
        ConflictType(differentGroupsSameLessonQuery,"Different groups have the same audience or teacher simultaneously")
    ]

    def findConflicts(self):
        if not self.isUpdated:
            for i in self.conflictsByTypes:
                tJoinL = self.tablesToJoinL
                for j in dbconnector.scheduleDB.tablesList:
                    tJoinL = tJoinL.replace(j, j[:-2]+'qeoijo')
                    tJoinL = tJoinL.replace(j[:-2]+'qeoijo', j + ' ' + j[:-2]+'qeoijo', 1)
                    self.selectedColumnsL = self.selectedColumnsL.replace(j, j[:-2]+'qeoijo')
                i.data = self.cur.execute(i.query % (self.selectedColumnsR, self.selectedColumnsL, self.tablesToJoinR, tJoinL)).fetchall()
                i.data = [ [k[:len(k)//2]] + [k[len(k)//2:]] for k in i.data]
        self.isUpdated = True
