# admin.py
from django.contrib import admin
from .models import Question, Choice, Student
from .forms import ExcelImportForm
import pandas as pd
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from docx import Document
from django.utils.timezone import now

# admin.site.register(Student)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    search_fields = ['unique_code', 'user__username']
    list_display = ['last_name', 'first_name', 'unique_code', 'score', 'login_time', 'test_start_time', 'test_end_time']
    actions = ['download_report']

    def download_report(self, request, queryset):
        # Проверяем, выбран ли хотя бы один студент
        if not queryset.exists():
            self.message_user(request, "Пожалуйста, выберите хотя бы одного студента.", level='error')
            return

        # Собираем ID выбранных студентов
        student_ids = queryset.values_list('id', flat=True)
        ids_str = ','.join(map(str, student_ids))

        # Формируем URL с параметрами ids и перенаправляем
        url = reverse('download_student_report') + f'?ids={ids_str}'
        return HttpResponseRedirect(url)

    download_report.short_description = "Скачать отчет в формате таблицы"

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = ExcelImportForm
    list_display = ['text', 'language', 'module', 'created_at']  # Показываем module вместо difficulty
    search_fields = ['text']
    list_filter = ['created_at', 'module']  # Фильтр по module
    save_as = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Импорт из Excel выполняется только если файл загружен
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            # Получаем имя файла без расширения
            file_name = excel_file.name.rsplit('.', 1)[0]  # Например, "module_1_hard_uz"
            df = pd.read_excel(excel_file)

            required_columns = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'language']
            if not all(col in df.columns for col in required_columns):
                self.message_user(request, "Excel-файл должен содержать столбцы: question_text, option_a, option_b, option_c, option_d, correct_option, language", level='error')
                return

            for _, row in df.iterrows():
                question = Question.objects.create(
                    text=row['question_text'],
                    language=row['language'],
                    module=file_name  # Сохраняем имя файла как module
                )
                Choice.objects.create(
                    question=question,
                    a=row['option_a'],
                    b=row['option_b'],
                    c=row['option_c'],
                    d=row['option_d'],
                    is_correct=row['correct_option']
                )
            self.message_user(request, f"Импортировано {len(df)} вопросов из файла {file_name}.")

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    search_fields = ['id', 'a', 'b', 'c', 'd']
    list_display = ['question', 'a', 'b', 'c', 'd', 'is_correct']
    save_as = True
# admin.site.register(Question)
# admin.site.register(Choice)
