import dbconnector

#constants
sameGroupDifferentLessonQuery = """SELECT * FROM SCHED_ITEMS r CROSS JOIN SCHED_ITEMS t WHERE 
r.LESSON_ID = t.LESSON_ID AND r.SUBJECT_ID = t.SUBJECT_ID AND r.GROUP_ID = t.GROUP_ID AND r.WEEKDAY_ID = t.WEEKDAY_ID 
AND (r.AUDIENCE_ID != t.AUDIENCE_ID OR r.TEACHER_ID != t.TEACHER_ID OR r.TYPE_ID != t.TYPE_ID) """

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

    conflicts = [
        ConflictType(sameGroupDifferentLessonQuery,"The same group has different lessons simultaneously")
    ]

    def findConflicts(self):
        if not self.isUpdated:
            for i in self.conflicts:
                i.data = self.cur.execute(i.query).fetchall()
                i.data = [ [k[:len(k)//2]] + [k[len(k)//2:]] for k in i.data]
                t = []
                prevID = None
                for j in i.data:
                    if (j[self.IDposition] == prevID):
                        t[len(t)-1] += [j]
                    else:
                        t.append([j])
                        prevID = j[self.IDposition]
                i.data = t.copy()