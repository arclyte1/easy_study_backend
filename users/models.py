from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from rest_framework.authtoken.models import Token


class MyUserManager(BaseUserManager):
    def create_user(self, email, name, role, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        if role not in User.Role.values:
            raise ValueError('Invalid role, available roles are ' + str(User.Role.values))

        user = self.model(
            name=name,
            role=role,
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, role, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            name=name,
            role=role,
            email=email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):

    class Role(models.TextChoices):
        STUDENT = 'ST', 'Student'
        TEACHER = 'TR', 'Teacher'

    email = models.EmailField(max_length=255, unique=True, blank=False)
    name = models.CharField(max_length=255, blank=False)
    role = models.CharField(max_length=255, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'role']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        """Does the user have permissions.py to view the app `app_label`?"""
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        # Simplest possible answer: All admins are staff
        return self.is_admin

    def update_data(self, name=None, role=None, password=None):
        if name:
            self.name = name
        if role and role in self.Role.values:
            self.role = role
        if password:
            self.set_password(password)
        self.save()


class StudyGroup(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    group_title = models.CharField(max_length=20, blank=False)
    subject_title = models.CharField(max_length=50, blank=False)
    students = models.ManyToManyField(User, related_name='studying_groups', blank=True)
    teachers = models.ManyToManyField(User, related_name='teaching_groups', blank=True)


class Lesson(models.Model):
    title = models.CharField(max_length=50, blank=False)
    date = models.DateTimeField(null=True, blank=True)
    group = models.ForeignKey(StudyGroup, related_name='lessons', on_delete=models.CASCADE)
    attendances = models.ManyToManyField(User, related_name='attendances', blank=True)


class Mark(models.Model):
    student = models.ForeignKey(User, related_name='marks', on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, related_name='marks', on_delete=models.CASCADE)
    mark = models.FloatField(blank=False)
