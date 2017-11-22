class Field:
    def __init__(self, type='int', width=1, name='Field'):
        self.type = type
        self.width = width
        self.name = name

class refField(Field):
    def __init__(self, type, width, name, refTable='', refKey='', refName=''):
        Field.__init__(self, type, width, name)
        self.refTable = refTable
        self.refKey = refKey
        self.refName = refName

class TableMeta:
    def isField(self, i):
        return (not callable(getattr(self, i)) and not i.startswith("__") and i.isupper())

    def get_meta(self):
        result = {}
        for i in dir(self):
            if self.isField(i):
                result[i] = getattr(self, i)
        return result

    def get_fields(self):
        result = []
        for i in dir(self):
            if self.isField(i):
                result.append(i)
        return result


class Audiences(TableMeta):
    ID = Field('int', 1, 'id')
    NAME = Field('string', 2, 'Номер аудитории')


class Lessons(TableMeta):
    ID = Field('int', 4, 'id')
    NAME = Field('string', 8, 'Название занятия')
    ORDER_NUMBER = Field('int', 4, 'id')


class Groups(TableMeta):
    ID = Field('int', 1, 'id')
    NAME = Field('string', 2, 'Номер группы')


class Lesson_Types(TableMeta):
    ID = Field('int', 1, 'id')
    NAME = Field('string', 2, 'Тип занятия')


class Sched_Items(TableMeta):
    ID = Field('int', 1, 'id')
    LESSON_ID = refField('ref', 2, 'Номер пары', 'LESSONS', 'ID', 'NAME')
    SUBJECT_ID = refField('ref', 2, 'Название предмета', 'SUBJECTS', 'ID', 'NAME')
    AUDIENCE_ID = refField('ref', 1, 'Номер аудитории', 'AUDIENCES', 'ID', 'NAME')
    GROUP_ID = refField('ref', 1, 'Номер группы', 'GROUPS', 'ID', 'NAME')
    TEACHER_ID = refField('ref', 2, 'Преподаватель', 'TEACHERS', 'ID', 'NAME')
    TYPE_ID = refField('ref', 1, 'Тип занятия', 'LESSON_TYPES', 'ID', 'NAME')
    WEEKDAY_ID = refField('ref', 2, 'День недели', 'WEEKDAYS', 'ID', 'NAME')


class Subjects(TableMeta):
    ID = Field('int', 1, 'id')
    NAME = Field('string', 2, 'Название предмета')


class Subject_Group(TableMeta):
    SUBJECT_ID = refField('ref', 2, 'Название предмета', 'SUBJECTS', 'ID', 'NAME')
    GROUP_ID = refField('ref', 2, 'Номер группы', 'GROUPS', 'ID', 'NAME')


class Subject_Teacher(TableMeta):
    SUBJECT_ID = refField('ref', 2, 'Название предмета', 'SUBJECTS', 'ID', 'NAME')
    TEACHER_ID = refField('ref', 2, 'Преподаватель', 'TEACHERS', 'ID', 'NAME')


class Teachers(TableMeta):
    ID = Field('int', 1, 'id')
    NAME = Field('string', 2, 'Преподаватель')


class Weekdays(TableMeta):
    ID = Field('int', 1, 'id')
    NAME = Field('string', 2, 'День недели')
    ORDER_NUMBER = Field('int', 1, 'Порядковый номер')


audiences = Audiences()
lessons = Lessons()
groups = Groups()
lesson_types = Lesson_Types()
sched_items = Sched_Items()
subjects = Subjects()
subject_group = Subject_Group()
subject_teacher = Subject_Teacher()
teachers = Teachers()
weekdays = Weekdays()
