# admin.py
from django.contrib import admin
from .models import Question, Choice, Student
from .forms import ExcelImportForm
import pandas as pd
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from docx import Document
from django.utils.timezone import now

# admin.site.register(Student)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    search_fields = ['unique_code', 'user__username']
    list_display = ['last_name', 'first_name', 'unique_code', 'score', 'login_time', 'test_start_time', 'test_end_time']
    actions = ['download_report']

    def download_report(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Пожалуйста, выберите только одного студента для генерации отчета.",
                              level='error')
            return
        student = queryset.first()
        return redirect('download_student_report', student_id=student.id)

    download_report.short_description = "Скачать отчет в формате Word"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:student_id>/download_report/', self.admin_site.admin_view(self.download_report_view),
                 name='download_student_report'),
        ]
        return custom_urls + urls

    def download_report_view(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        doc = Document()
        doc.add_heading('Отчет', level=1)

        doc.add_paragraph(f'Имя: {student.first_name}')
        doc.add_paragraph(f'Фамилия: {student.last_name}')
        doc.add_paragraph(f'Отчество: {student.middle_name or "Не указано"}')
        doc.add_paragraph(f'Уникальный код: {student.unique_code}')
        doc.add_paragraph(f'Баллы: {student.score}')

        doc.add_paragraph(
            f'Время входа: {student.login_time.strftime("%Y-%m-%d %H:%M:%S") if student.login_time else "Не указано"}')
        doc.add_paragraph(
            f'Время начала теста: {student.test_start_time.strftime("%Y-%m-%d %H:%M:%S") if student.test_start_time else "Не указано"}')
        doc.add_paragraph(
            f'Время окончания теста: {student.test_end_time.strftime("%Y-%m-%d %H:%M:%S") if student.test_end_time else "Не указано"}')

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=report_{student.unique_code}.docx'
        doc.save(response)
        return response

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = ExcelImportForm
    list_display = ['text', 'language', 'created_at']
    search_fields = ['text']
    list_filter = ['created_at']
    save_as = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if 'excel_file' in request.FILES:
            # Чтение Excel-файла
            df = pd.read_excel(request.FILES['excel_file'])

            # Проверка наличия необходимых столбцов
            required_columns = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'language']
            if not all(col in df.columns for col in required_columns):
                self.message_user(request, "Excel-файл должен содержать столбцы: question_text, option_a, option_b, option_c, option_d, correct_option, language", level='error')
                return

            # Создание вопросов и вариантов
            for _, row in df.iterrows():
                question = Question.objects.create(
                    text=row['question_text'],
                    language=row['language']
                )
                a = Question.objects.all()
                print(a)
                Choice.objects.create(
                    question=question,
                    a=row['option_a'],
                    b=row['option_b'],
                    c=row['option_c'],
                    d=row['option_d'],
                    is_correct=row['correct_option']
                )
                b = Choice.objects.all()
                print(b)
            self.message_user(request, f"Импортировано {len(df)} вопросов.")

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    search_fields = ['id', 'a', 'b', 'c', 'd']
    list_display = ['question', 'a', 'b', 'c', 'd', 'is_correct']
    save_as = True
# admin.site.register(Question)
# admin.site.register(Choice)
