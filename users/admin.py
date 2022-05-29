from django.contrib import admin
from users.models import User, StudyGroup, Lesson, Mark

admin.site.register(User)
admin.site.register(StudyGroup)
admin.site.register(Lesson)
admin.site.register(Mark)
