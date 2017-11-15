class Meta:
    def __init__(self, type='int', width=1, name='Field', refTable='', refKey='', refName=''):
        self.type = type
        self.width = width
        self.name = name
        self.refTable = refTable
        self.refKey = refKey
        self.refName = refName


class BaseTable:
    def get_meta(self):
        result = {}
        for i in dir(self):
            if not callable(getattr(self, i)) and not i.startswith("__") and i.isupper():
                result[i] = getattr(self, i)
        return result


class Audiences(BaseTable):
    ID = Meta('int', '1', 'id')
    NAME = Meta('string', '2', 'Номер аудитории')


class Lessons(BaseTable):
    ID = Meta('int', '4', 'id')
    NAME = Meta('string', '8', 'Название занятия')
    ORDER_NUMBER = Meta('int', '4', 'id')


class Groups(BaseTable):
    ID = Meta('int', '1', 'id')
    NAME = Meta('string', '2', 'Номер группы')


class LessonTypes(BaseTable):
    ID = Meta('int', '1', 'id')
    NAME = Meta('string', '2', 'Тип занятия')


class Sched_Items(BaseTable):
    ID = Meta('int', '1', 'id')
    LESSON_ID = Meta('ref', '2', 'Номер пары', 'LESSONS', 'ID', 'NAME')
    SUBJECT_ID = Meta('ref', '2', 'Название предмета', 'SUBJECTS', 'ID', 'NAME')
    AUDIENCE_ID = Meta('ref', '1', 'Номер аудитории', 'AUDIENCES', 'ID', 'NAME')
    GROUP_ID = Meta('ref', '1', 'Номер группы', 'GROUPS', 'ID', 'NAME')
    TEACHER_ID = Meta('ref', '2', 'Преподаватель', 'TEACHERS', 'ID', 'NAME')
    TYPE_ID = Meta('ref', '1', 'Тип занятия', 'LESSON_TYPES', 'ID', 'NAME')
    WEEKDAY_ID = Meta('ref', '2', 'День недели', 'WEEKDAYS', 'ID', 'NAME')


class Subjects(BaseTable):
    ID = Meta('int', '1', 'id')
    NAME = Meta('string', '2', 'Название предмета')


class SubjectGroup(BaseTable):
    SUBJECT_ID = Meta('ref', '2', 'Название предмета', 'SUBJECTS', 'ID', 'NAME')
    GROUP_ID = Meta('ref', '2', 'Номер группы', 'GROUPS', 'ID', 'NAME')


class SubjectTeacher(BaseTable):
    SUBJECT_ID = Meta('ref', '2', 'Название предмета', 'SUBJECTS', 'ID', 'NAME')
    TEACHER_ID = Meta('ref', '2', 'Преподаватель', 'TEACHERS', 'ID', 'NAME')


class Teachers(BaseTable):
    ID = Meta('int', '1', 'id')
    NAME = Meta('string', '2', 'Преподаватель')


class Weekdays(BaseTable):
    ID = Meta('int', '1', 'id')
    NAME = Meta('string', '2', 'День недели')
    ORDER_NUMBER = Meta('int', '1', 'Порядковый номер')


audiences = Audiences()
lessons = Lessons()
groups = Groups()
lesson_types = LessonTypes()
sched_items = Sched_Items()
subjects = Subjects()
subject_group = SubjectGroup()
subject_teacher = SubjectTeacher()
teachers = Teachers()
weekdays = Weekdays()
