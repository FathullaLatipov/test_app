from django.shortcuts import render, redirect
from .models import Question, Student, Choice
from django.contrib.auth.models import User
from django.contrib.auth import login
from .forms import StudentRegistrationForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required

def register_student(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["first_name"],  # Или другой уникальный идентификатор
                password=form.cleaned_data["password"]
            )
            student = form.save(commit=False)
            student.user = user  # Привязываем пользователя
            student.save()
            login(request, user)

            return redirect("home")
    else:
        form = StudentRegistrationForm()
    return render(request, "register.html", {"form": form})

def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")  # Используем username
        password = request.POST.get("password")
        student = authenticate(request, username=username, password=password)  # Здесь username
        if student is not None:
            login(request, student)
            return redirect("home")  # Редирект на домашнюю страницу
        else:
            return render(request, "login.html", {"error": "Неверные данные"})
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

    if total_questions == 0:
        question = None
        selected_answer = None
    else:
        current_question = max(1, min(current_question, total_questions))
        question = questions[current_question - 1]
        # Получаем выбранный ответ для текущего вопроса из сессии
        selected_answer = request.session.get('answers', {}).get(f'answer_{question.id}')

    user = request.user
    student, created = Student.objects.get_or_create(user=user)

    # Инициализация ответов в сессии, если их нет
    if 'answers' not in request.session:
        request.session['answers'] = {}

    print(f"Session answers for question {current_question}: {request.session.get('answers', {})}")
    print(f"Selected answer for question {question.id if question else 'none'}: {selected_answer}")

    # Обработка отправки теста
    if request.method == 'POST' and 'submit_quiz' in request.POST:
        submitted_answers = request.session.get('answers', {}).copy()
        print(f"Submitted answers: {submitted_answers}")

        # Проверяем, есть ли хотя бы один ответ
        if not submitted_answers:
            # Если ответов нет, показываем предупреждение и возвращаем на главную страницу
            return render(request, 'index.html', {
                'question': question,
                'current_language': language,
                'user': user,
                'current_question': current_question,
                'total_questions': total_questions,
                'initial_time': 3600,
                'answers': request.session.get('answers', {}),
                'selected_answer': selected_answer,
                'error': 'Вы не ответили ни на один вопрос. Тест не будет завершен.'
            })

        correct_count = 0
        user_answers = []

        for q_id, answer in submitted_answers.items():
            if q_id.startswith('answer_'):
                question_id = q_id.replace('answer_', '')
                try:
                    if not question_id.isdigit():
                        continue
                    question_id = int(question_id)
                    q = Question.objects.get(id=question_id)
                    choice = q.choices.first()
                    if choice:
                        correct_answer = choice.is_correct
                        user_answer = {
                            'question_text': q.text,
                            'user_answer': answer,
                            'correct_answer': correct_answer,
                            'is_correct': choice.is_correct == answer
                        }
                        user_answers.append(user_answer)
                        if choice.is_correct == answer:
                            correct_count += 1
                except (Question.DoesNotExist, ValueError):
                    continue

        score = (correct_count / total_questions) * 50 if total_questions > 0 else 0
        student.score = score
        student.save()

        # Очистка сессии после отправки
        request.session['answers'] = {}
        request.session.modified = True

        # Перенаправляем на страницу результатов
        return render(request, 'results.html', {
            'score': score,
            'total_questions': total_questions,
            'current_language': language,
            'user': user,
            'user_answers': user_answers
        })

    initial_time = 3600  # 1 час в секундах

    if 'timer_reset' in request.GET:
        request.session['answers'] = {}
        request.session.modified = True

    return render(request, 'index.html', {
        'question': question,
        'current_language': language,
        'user': user,
        'current_question': current_question,
        'total_questions': total_questions,
        'initial_time': initial_time,
        'answers': request.session.get('answers', {}),
        'selected_answer': selected_answer
    })


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