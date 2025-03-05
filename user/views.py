from django.shortcuts import render, redirect, get_object_or_404
from .models import Question, Student, Choice
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .forms import StudentRegistrationForm
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
import time
from django.contrib import messages
from docx import Document
from openpyxl import Workbook
import openpyxl
from django.utils.timezone import now

def register_student(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            password = form.cleaned_data["password"]
            student = form.save(commit=False)
            student.save()
            unique_username = student.unique_code
            user = User.objects.create_user(
                username=unique_username,
                password=password,
                first_name=first_name
            )
            student.user = user
            student.save()
            request.session['expected_unique_code'] = student.unique_code
            request.session['user_id'] = user.id
            # Сбрасываем таймер для нового пользователя
            request.session[f'timer_start_{user.id}'] = int(time.time() * 1000)  # Время в миллисекундах
            return render(request, "verify_unique_code.html", {"form": form})
    else:
        form = StudentRegistrationForm()
    return render(request, "register.html", {"form": form})

def verify_unique_code(request):
    if request.method == "POST":
        entered_code = request.POST.get("unique_code")
        expected_code = request.session.get("expected_unique_code")  # Используем .get() для безопасного доступа
        user_id = request.session.get("user_id")  # Используем .get() для безопасного доступа

        if entered_code and expected_code and user_id:
            if entered_code == expected_code:
                user = User.objects.get(id=user_id)
                student = user.student  # Получаем связанный объект Student
                student.login_time = now()
                student.save()
                login(request, user)
                # Удаляем сессионные данные, только если они существуют
                if 'expected_unique_code' in request.session:
                    del request.session['expected_unique_code']
                if 'user_id' in request.session:
                    del request.session['user_id']
                return redirect("home")
            else:
                return render(request, "verify_unique_code.html", {
                    "error": "Неверный уникальный код. Попробуйте снова."
                })
        else:
            return render(request, "verify_unique_code.html", {
                "error": "Сессия истекла или данные недоступны. Пожалуйста, начните регистрацию заново."
            })
    return redirect("register")

def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            student = user.student  # Получаем связанный объект Student
            student.login_time = now()  # Логируем время входа
            student.save()
            return redirect("home")
        else:
            # Добавляем сообщение об ошибке через messages
            messages.error(request, "Неверные данные. Проверьте имя пользователя и пароль.")
            return render(request, "login.html")
    return render(request, "login.html")

def student_logout(request):
    logout(request)
    return redirect('login')
#
# def dashboard(request):
#     return render(request, 'dashboard.html', {'user': request.user})

@login_required
def quiz_list(request):
    language = request.GET.get('lang', 'uz')
    current_question = request.GET.get('q', '1')

    try:
        current_question = int(current_question)
    except ValueError:
        current_question = 1

    questions = Question.objects.filter(language=language).prefetch_related('choices')
    total_questions = questions.count()
    question_list = [{'id': q.id, 'text': q.text} for q in questions]

    if total_questions == 0:
        question = None
        selected_answer = None
    else:
        current_question = max(1, min(current_question, total_questions))
        question = questions[current_question - 1]
        selected_answer = request.session.get('answers', {}).get(f'answer_{question.id}')

    user = request.user
    student, created = Student.objects.get_or_create(user=user)

    if not student.test_start_time and not student.test_end_time:
        # Устанавливаем время начала теста, если оно ещё не установлено
        student.test_start_time = now()
        student.save()
        request.session[f'timer_start_{user.id}'] = int(time.time() * 1000)
        request.session.modified = True

    if 'answers' not in request.session:
        request.session['answers'] = {}

    # Передаем начальное время таймера из сессии
    start_time = request.session.get(f'timer_start_{user.id}')

    if request.method == 'POST' and 'submit_quiz' in request.POST:
        submitted_answers = request.session.get('answers', {}).copy()
        correct_count = 0
        user_answers = []

        # Обрабатываем все вопросы, даже если на них не ответили
        for q in questions:
            q_id = f'answer_{q.id}'
            answer = submitted_answers.get(q_id, None)  # Если ответа нет, None
            choice = q.choices.first()
            if choice:
                correct_answer = choice.is_correct
                is_correct = (answer == correct_answer) if answer else False  # Неотвеченный = неверный
                user_answer = {
                    'question_text': q.text,
                    'user_answer': answer if answer else "Не отвечено",
                    'correct_answer': correct_answer,
                    'is_correct': is_correct
                }
                user_answers.append(user_answer)
                if is_correct:
                    correct_count += 1

        score = (correct_count / total_questions) * 50 if total_questions > 0 else 0
        student.score = score
        student.test_end_time = now()
        student.save()
        request.session['answers'] = {}
        request.session.modified = True
        # Сбрасываем таймер после завершения теста
        if f'timer_start_{user.id}' in request.session:
            del request.session[f'timer_start_{user.id}']
        return render(request, 'results.html', {
            'score': score,
            'total_questions': total_questions,
            'total_score': score * 2,
            'current_language': language,
            'user': user,
            'user_answers': user_answers
        })

    initial_time = 3600
    if 'timer_reset' in request.GET:
        request.session['answers'] = {}
        if f'timer_start_{user.id}' in request.session:
            del request.session[f'timer_start_{user.id}']
        request.session.modified = True

    return render(request, 'index.html', {
        'question': question,
        'current_language': language,
        'user': user,
        'current_question': current_question,
        'total_questions': total_questions,
        'initial_time': initial_time,
        'answers': request.session.get('answers', {}),
        'selected_answer': selected_answer,
        'question_list': question_list,
        'start_time': request.session.get(f'timer_start_{user.id}')
    })

@login_required
def set_timer(request):
    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        if start_time:
            request.session[f'timer_start_{request.user.id}'] = int(start_time)
            request.session.modified = True
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'method not allowed'}, status=405)


MONTHS = {
    'January': 'Январь',
    'February': 'Февраль',
    'March': 'Март',
    'April': 'Апрель',
    'May': 'Май',
    'June': 'Июнь',
    'July': 'Июль',
    'August': 'Август',
    'September': 'Сентябрь',
    'October': 'Октябрь',
    'November': 'Ноябрь',
    'December': 'Декабрь'
}

@login_required
def download_student_report(request):
    ids_str = request.GET.get('ids', '')
    student_ids = [int(id) for id in ids_str.split(',') if id.isdigit()]

    if not student_ids:
        return HttpResponse("Не выбрано ни одного студента.", status=400)

    students = Student.objects.filter(id__in=student_ids)

    # Создаем Excel-файл
    wb = Workbook()
    ws = wb.active
    ws.title = "Студенты"

    # Заголовки таблицы
    headers = ['Фамилия', 'Имя', 'Уникальный код', 'Баллы', 'Время входа', 'Время начала теста', 'Время окончания теста']
    for col_num, header in enumerate(headers, 1):
        ws[f'{chr(64 + col_num)}1'] = header
        ws[f'{chr(64 + col_num)}1'].font = openpyxl.styles.Font(bold=True)


    # Заполняем данными студентов
    for row_num, student in enumerate(students, 2):
        ws[f'A{row_num}'] = student.last_name
        ws[f'B{row_num}'] = student.first_name
        ws[f'C{row_num}'] = student.unique_code
        ws[f'D{row_num}'] = student.score
        if student.login_time:
            # Форматируем дату с заменой месяца на русский
            date_str = student.login_time.strftime("%d %B %Y г. %H:%M")
            month = student.login_time.strftime("%B")
            date_str = date_str.replace(month, MONTHS[month])
            ws[f'E{row_num}'] = date_str
        else:
            ws[f'E{row_num}'] = 'Не указано'
        if student.test_start_time:
            # Форматируем дату с заменой месяца на русский
            date_str = student.test_start_time.strftime("%d %B %Y г. %H:%M")
            month = student.test_start_time.strftime("%B")
            date_str = date_str.replace(month, MONTHS[month])
            ws[f'F{row_num}'] = date_str
        else:
            ws[f'F{row_num}'] = 'Не указано'
        if student.test_end_time:
            # Форматируем дату с заменой месяца на русский
            date_str = student.test_end_time.strftime("%d %B %Y г. %H:%M")
            month = student.test_end_time.strftime("%B")
            date_str = date_str.replace(month, MONTHS[month])
            ws[f'G{row_num}'] = date_str
        else:
            ws[f'G{row_num}'] = 'Не указано'

    for col in ws.columns:
        max_length = max(len(str(cell.value)) for cell in col if cell.value)
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    # Настраиваем ответ для скачивания
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=students_report.xlsx'
    wb.save(response)
    return response

@require_POST
@login_required
def save_answer(request):
    question_id = request.POST.get('question_id')
    answer = request.POST.get('answer')
    if question_id and answer and question_id.isdigit():
        if 'answers' not in request.session:
            request.session['answers'] = {}

        # Сохраняем ответ в сессии
        request.session['answers'][f'answer_{question_id}'] = answer
        request.session.modified = True
        print(f"Saved answer for question {question_id}: {answer}")  # Отладка
        print(f"Session after save: {request.session.get('answers')}")  # Дополнительная отладка

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)