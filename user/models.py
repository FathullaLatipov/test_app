from django.db import models
import random
import string
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission


def generate_unique_code():
    """Генерация гарантированно уникального 4-значного кода"""
    while True:
        code = ''.join(random.choices(string.digits, k=4))
        if not Student.objects.filter(unique_code=code).exists():
            return code

class Student(models.Model):
    first_name = models.CharField(max_length=100, verbose_name=_('Имя'))
    last_name = models.CharField(max_length=100, verbose_name=_('Фамилия'))
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Отчество'))
    unique_code = models.CharField(
        max_length=4,
        unique=True,
        default=generate_unique_code,
        editable=False,
        verbose_name=_('Уникальный код')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))

    def __str__(self):
        return f'{self.last_name} {self.first_name} {self.middle_name or ""} ({self.unique_code})'

    class Meta:
        verbose_name = _('Студент')
        verbose_name_plural = _('Студенты')

# class StudentManager(BaseUserManager):
#     """Менеджер для создания пользователей и суперпользователей"""
#
#     def create_user(self, first_name, last_name, patronymic_name, email, password=None):
#         if not email:
#             raise ValueError('Email обязателен')
#         email = self.normalize_email(email)
#         user = self.model(
#             first_name=first_name,
#             last_name=last_name,
#             patronymic_name=patronymic_name,
#             email=email,
#             unique_code=generate_unique_code()
#         )
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, first_name, last_name, patronymic_name, email, password):
#         user = self.create_user(first_name, last_name, patronymic_name, email, password)
#         user.is_superuser = True
#         user.is_staff = True
#         user.save(using=self._db)
#         return user
#
#
# class Student(AbstractBaseUser, PermissionsMixin):
#     """Модель студента"""
#
#     first_name = models.CharField(max_length=60, verbose_name=_('Имя'))
#     last_name = models.CharField(max_length=70, verbose_name=_('Фамилия'))
#     patronymic_name = models.CharField(max_length=100, verbose_name=_('Отчество'))
#     email = models.EmailField(unique=True, verbose_name=_('Email'))
#     unique_code = models.CharField(max_length=4, unique=True, editable=False, default=generate_unique_code)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)
#
#     groups = models.ManyToManyField(Group, related_name="student_groups", blank=True)
#     user_permissions = models.ManyToManyField(Permission, related_name="student_permissions", blank=True)
#
#     objects = StudentManager()
#
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['first_name', 'last_name', 'patronymic_name']
#
#     def __str__(self):
#         return f"{self.first_name} {self.last_name} ({self.unique_code})"
#
#     class Meta:
#         verbose_name = _('Студент')
#         verbose_name_plural = _('Студенты')

class Question(models.Model):
    LANGUAGE_CHOICES = (
        ('uz', 'Uzbek'),
        ('ru', 'Russian'),
    )

    text = models.TextField()
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.text} ({self.language})"

    class Meta:
        verbose_name = _('Тест')
        verbose_name_plural = _('Тесты')

class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    a = models.TextField(blank=True)  # Option A
    b = models.TextField(blank=True)  # Option B
    c = models.TextField(blank=True)  # Option C
    d = models.TextField(blank=True)  # Option D
    is_correct = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')], default='a')  # Correct option (a, b, c, or d)

    def __str__(self):
        return f"Варианты для {self.question.text}"

    class Meta:
        verbose_name = _('Вариант')
        verbose_name_plural = _('Варианты')