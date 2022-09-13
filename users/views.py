from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils.dateparse import parse_datetime
from users.models import User, StudyGroup, Lesson, Mark
from users.serializers import UserSerializer, StudyGroupSerializer, LessonSerializer, StudentLessonSerializer, \
    MarkSerializer, SimpleUserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('email')
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserAuthentication(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        """
        Authentication for users
        """
        response = super().post(request, *args, **kwargs)
        if 200 <= response.status_code <= 299:
            user = User.objects.get(email=request.data['email'])
            response.data |= UserSerializer(user).data
        return response


class UserRegistration(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Registration for users
        """
        data = request.data
        try:
            user = User.objects.create_user(email=data['email'],
                                            name=data['name'],
                                            role=data['role'],
                                            password=data['password'])
            access = AccessToken.for_user(user)
            refresh = RefreshToken.for_user(user)
            return Response(data=(dict(UserSerializer(user).data) | {'password': data['password'],
                                                                     'access': str(access),
                                                                     'refresh': str(refresh)
                                                                     }))
        except Exception as e:
            return Response(data={'error': type(e).__name__, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    def get(self, request):
        """
        Current user info by access token
        """
        return Response(data=UserSerializer(request.user).data)

    def put(self, request):
        """
        Updating current user information
        Allowed fields: name, role, password
        """
        allowed_fields = ['name', 'role', 'password']
        for field in allowed_fields:
            if field not in request.data:
                request.data[field] = None
        request.user.update_data(name=request.data['name'],
                                 role=request.data['role'],
                                 password=request.data['password'])
        return Response(data=(dict(UserSerializer(request.user).data) | ({'password': request.data['password']} if
                                                                         request.data['password'] else {})))


class GroupList(APIView):
    def get(self, request):
        if request.user.role == User.Role.STUDENT:
            return Response(data=StudyGroupSerializer(request.user.studying_groups, many=True).data)
        elif request.user.role == User.Role.TEACHER:
            return Response(data=StudyGroupSerializer(request.user.teaching_groups, many=True).data)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            group = StudyGroup(group_title=request.data['group_title'],
                               subject_title=request.data['subject_title'])
            group.save()
            group.teachers.add(request.user)
            group.save()
            return Response(data=StudyGroupSerializer(group).data)
        except Exception:
            return Response(data={'group_title': 'required', 'subject_title': 'required'},
                            status=status.HTTP_400_BAD_REQUEST)


class GroupDetail(APIView):
    def put(self, request, pk):
        try:
            group = StudyGroup.objects.get(id=pk)
            if group.teachers.filter(id=request.user.id).exists():
                if 'group_title' in request.data:
                    group.group_title = request.data['group_title']
                if 'subject_title' in request.data:
                    group.subject_title = request.data['subject_title']
                group.save()
                return Response(data=StudyGroupSerializer(group).data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            group = StudyGroup.objects.get(id=pk)
            if group.teachers.filter(id=request.user.id).exists():
                group.delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


class LessonList(APIView):
    def get(self, request, group_id):
        try:
            group = StudyGroup.objects.get(id=group_id)

            if group.teachers.filter(id=request.user.id).exists():
                return Response(data=list(LessonSerializer(lesson).data for lesson in group.lessons.all()))

            if group.students.filter(id=request.user.id).exists():
                data = list()
                for lesson in group.lessons.all():
                    item = StudentLessonSerializer(lesson).data
                    item |= {'attendance': lesson.attendances.filter(id=request.user.id).exists()}
                    try:
                        item |= {'mark': lesson.marks.filter(student_id=request.user.id).get().mark}
                    except Mark.DoesNotExist:
                        item |= {'mark': None}
                    data.append(item)
                return Response(data=data)

            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request, group_id):
        try:
            if StudyGroup.objects.get(id=group_id).teachers.filter(id=request.user.id).exists():
                lesson = Lesson(title=request.data['title'],
                                date=parse_datetime(request.data['date']) if 'date' in request.data else None,
                                group_id=group_id)
                lesson.save()
                return Response(data=LessonSerializer(lesson).data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


class LessonDetail(APIView):
    def put(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            if lesson.group.teachers.filter(id=request.user.id).exists():
                if 'title' in request.data:
                    lesson.title = request.data['title']
                if 'date' in request.data:
                    lesson.date = parse_datetime(request.data['date'])
                lesson.save()
                return Response(data=LessonSerializer(lesson).data)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response(data=str(e),
                            status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            if lesson.group.teachers.filter(id=request.user.id).exists():
                lesson.delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


class MarkList(APIView):
    def post(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            if lesson.group.teachers.filter(id=request.user.id).exists():
                try:
                    mark = lesson.marks.filter(student_id=request.data['student']).get()
                    mark.mark = request.data['mark']
                except Mark.DoesNotExist:
                    mark = Mark(student_id=request.data['student'],
                                lesson_id=lesson_id,
                                mark=request.data['mark'])
                mark.save()
                return Response(data=MarkSerializer(mark).data)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            if lesson.group.teachers.filter(id=request.user.id).exists():
                lesson.marks.filter(student_id=request.data['student']).delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


class AttendanceList(APIView):
    def post(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            if lesson.group.teachers.filter(id=request.user.id).exists():
                if request.data['attendance']:
                    lesson.attendances.add(User.objects.get(id=request.data['student']))
                else:
                    lesson.attendances.remove(User.objects.get(id=request.data['student']))
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


class AddStudent(APIView):
    def post(self, request, group_id):
        try:
            group = StudyGroup.objects.get(id=group_id)
            if not User.objects.filter(email=request.data['email']).exists():
                return Response(status=status.HTTP_403_FORBIDDEN)
            student = User.objects.get(email=request.data['email'])

            if not group.students.filter(id=student.id).exists() \
                    and group.teachers.filter(id=request.user.id).exists():
                group.students.add(student)
                group.save()
                return Response(data=StudyGroupSerializer(group).data,
                                status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


class AddTeacher(APIView):
    def post(self, request, group_id):
        try:
            group = StudyGroup.objects.get(id=group_id)
            if not User.objects.filter(email=request.data['email']).exists():
                return Response(status=status.HTTP_403_FORBIDDEN)
            teacher = User.objects.get(email=request.data['email'])

            if not group.teachers.filter(id=teacher.id).exists() \
                    and group.teachers.filter(id=request.user.id).exists():
                group.teachers.add(teacher)
                group.save()
                return Response(data=StudyGroupSerializer(group).data,
                                status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


class StudentList(APIView):
    def get(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            students = list()
            for student in lesson.group.students.all():
                item = SimpleUserSerializer(student).data
                lesson.marks.filter(student_id=student.id).exists()
                item |= {
                    'attendance': True if lesson.attendances.filter(id=student.id).exists() else False,
                    'mark': lesson.marks.filter(student_id=student.id).get().mark if
                    lesson.marks.filter(student_id=student.id).exists() else None}
                students.append(item)

            return Response(data=students)
        except Exception as e:
            return Response(data=str(e), status=status.HTTP_404_NOT_FOUND)


class StudentProgress(APIView):
    def get(self, request, group_id):
        try:
            email = request.GET.get('email', '')
            group = StudyGroup.objects.get(id=group_id)
            if group.students.filter(email=email).exists() \
                    and group.teachers.filter(id=request.user.id).exists():
                studentId = group.students.get(email=email).id
                data = list()
                for lesson in group.lessons.all():
                    item = StudentLessonSerializer(lesson).data
                    item |= {'attendance': lesson.attendances.filter(id=studentId).exists()}
                    try:
                        item |= {'mark': lesson.marks.filter(student_id=studentId).get().mark}
                    except Mark.DoesNotExist:
                        item |= {'mark': None}
                    data.append(item)
                return Response(data=data)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)
