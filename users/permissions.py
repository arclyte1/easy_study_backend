from rest_framework.permissions import BasePermission

from users.models import Lesson


class IsStudyingLesson(BasePermission):
    def has_permission(self, request, view):
        lesson = Lesson.objects.get(pk=request.data['id'])
        group = lesson.group
        return group in request.user.studying_groups
