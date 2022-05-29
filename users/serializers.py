from rest_framework import serializers
from users.models import User, StudyGroup, Lesson, Mark


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name']


class StudyGroupSerializer(serializers.ModelSerializer):
    students = SimpleUserSerializer(read_only=True, many=True)
    teachers = SimpleUserSerializer(read_only=True, many=True)

    class Meta:
        model = StudyGroup
        fields = ['id', 'group_title', 'subject_title', 'students', 'teachers', 'lessons']

#
# class StudentStudyGroupSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StudyGroup
#         fields = ['id', 'group_title', 'subject_title', 'students', 'teachers', 'lessons']


class MarkSerializer(serializers.ModelSerializer):
    student = SimpleUserSerializer(read_only=True, many=False)

    class Meta:
        model = Mark
        fields = ['id', 'student', 'lesson', 'mark']


class LessonSerializer(serializers.ModelSerializer):
    marks = MarkSerializer(read_only=True, many=True)
    attendances = SimpleUserSerializer(read_only=True, many=True)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'date', 'group', 'marks', 'attendances']


class StudentLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'date', 'group']


class UserSerializer(serializers.ModelSerializer):
    studying_groups = StudyGroupSerializer(read_only=True, many=True)
    teaching_groups = StudyGroupSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'last_login',
                  'studying_groups', 'teaching_groups', 'marks', 'attendances']
