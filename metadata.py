class Meta:
    def __init__(self, type='int', width=1, name='Field'):
        self.type = type
        self.width = width
        self.name = name

class BaseTable:
    def get_meta(self):
        result = {}
        for i in dir(self):
            if not callable(getattr(self, i)) and not i.startswith("__") and i.isupper():
                result[i]=getattr(self,i)
        return result

class Audiences(BaseTable):
    ID = Meta('int','1','id')
    NAME = Meta('string','2','Номер аудитории')

class Lessons(BaseTable):
    ID = Meta('int','4','id')
    NAME = Meta('string','8','Название занятия')
    ORDER_NUMBER = Meta('int', '4', 'id')

class Groups(BaseTable):
    ID = Meta('int','1','id')
    NAME = Meta('string','2','Номер группы')

class LessonTypes(BaseTable):
    ID = Meta('int','1','id')
    NAME = Meta('string','2','Тип занятия')

audiences = Audiences()
lessons = Lessons()
groups = Groups()
lessonTypes = LessonTypes()