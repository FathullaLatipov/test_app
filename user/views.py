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
import time
from django.contrib import messages

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
        expected_code = request.session.get("expected_unique_code")
        user_id = request.session.get("user_id")

        if entered_code == expected_code and user_id:
            user = User.objects.get(id=user_id)
            login(request, user)
            # Очищаем сессию после успешной проверки
            del request.session['expected_unique_code']
            del request.session['user_id']
            return redirect("home")
        else:
            return render(request, "verify_unique_code.html", {
                "error": "Неверный уникальный код. Попробуйте снова."
            })
    return redirect("register")

def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
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

    if 'answers' not in request.session:
        request.session['answers'] = {}

    # Передаем начальное время таймера из сессии
    start_time = request.session.get(f'timer_start_{user.id}')

    if request.method == 'POST' and 'submit_quiz' in request.POST:
        submitted_answers = request.session.get('answers', {}).copy()
        if len(submitted_answers) < total_questions:
            return render(request, 'index.html', {
                'question': question,
                'current_language': language,
                'user': user,
                'current_question': current_question,
                'total_questions': total_questions,
                'initial_time': 3600,
                'answers': request.session.get('answers', {}),
                'selected_answer': selected_answer,
                'question_list': question_list,
                'warning': 'Вы ответили не на все вопросы. Вы уверены, что хотите завершить тест?',
                'show_confirm': True,
                'start_time': start_time
            })

        if 'confirm_submit' in request.POST or len(submitted_answers) == total_questions:
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
            request.session['answers'] = {}
            request.session.modified = True
            # Сбрасываем таймер после завершения теста
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
        'start_time': start_time  # Передаем время начала
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