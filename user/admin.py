# admin.py
from django.contrib import admin
from .models import Question, Choice
from .forms import ExcelImportForm
import pandas as pd

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
                Choice.objects.create(
                    question=question,
                    a=row['option_a'],
                    b=row['option_b'],
                    c=row['option_c'],
                    d=row['option_d'],
                    is_correct=row['correct_option']
                )
            self.message_user(request, f"Импортировано {len(df)} вопросов.")

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    search_fields = ['id', 'a', 'b', 'c', 'd']
    list_display = ['question', 'a', 'b', 'c', 'd', 'is_correct']
    save_as = True
# admin.site.register(Question)
# admin.site.register(Choice)
