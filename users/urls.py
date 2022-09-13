from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)


router = DefaultRouter()
router.register('users', views.UserViewSet)

urlpatterns = [
    path('', include(router.urls)),

    path('registration/', views.UserRegistration.as_view()),
    path('login/', views.UserAuthentication.as_view(), name='token_obtain_pair'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-token/', TokenVerifyView.as_view(), name='token_verify'),
    path('me/', views.CurrentUserView.as_view()),
    path('groups/', views.GroupList.as_view()),
    path('groups/<int:pk>/', views.GroupDetail.as_view()),
    path('groups/<int:group_id>/students/', views.AddStudent.as_view()),
    path('groups/<int:group_id>/teachers/', views.AddTeacher.as_view()),
    path('groups/<int:group_id>/lessons/', views.LessonList.as_view()),
    path('groups/<int:group_id>/student_progress/', views.StudentProgress.as_view()),
    path('lessons/<int:lesson_id>/', views.LessonDetail.as_view()),
    path('lessons/<int:lesson_id>/marks/', views.MarkList.as_view()),
    path('lessons/<int:lesson_id>/attendances/', views.AttendanceList.as_view()),
    path('lessons/<int:lesson_id>/students/', views.StudentList.as_view()),
]
