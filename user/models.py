from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class Student(models.Model):
    full_name = models.CharField(max_length=200, verbose_name=_('ФИО'))  # ФИО студента
    unique_code = models.CharField(
        max_length=36,
        unique=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('Уникальный код')
    )  # Индивидуальный код
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))

    def __str__(self):
        return f"{self.full_name} ({self.unique_code})"

    class Meta:
        verbose_name = _('Студент')
        verbose_name_plural = _('Студенты')


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