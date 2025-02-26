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
    questions = Question.objects.filter(language=language).prefetch_related('choices')
    total_questions = questions.count()
    current_question = request.GET.get('q', '1')

    try:
        current_question = int(current_question)
        if current_question < 1 or current_question > total_questions:
            current_question = 1
    except ValueError:
        current_question = 1

    question = questions[current_question - 1] if questions else None
    user = request.user
    student, created = Student.objects.get_or_create(user=user)

    # Initialize session answers if not present
    if 'answers' not in request.session:
        request.session['answers'] = {}

    # Handle quiz submission
    if request.method == 'POST' and 'submit_quiz' in request.POST:
        print(f"Submitting quiz: POST data = {request.POST}")  # Для отладки
        submitted_answers = request.session.get('answers', {}).copy()
        correct_count = 0

        for q_id, answer in submitted_answers.items():
            if q_id.startswith('answer_'):
                question_id = q_id.replace('answer_', '')
                try:
                    q = Question.objects.get(id=question_id)
                    choice = q.choices.first()
                    if choice and choice.is_correct == answer:
                        correct_count += 1
                except Question.DoesNotExist:
                    pass

        score = (correct_count / total_questions) * 50 if total_questions > 0 else 0
        student.score = score
        student.save()

        # Clear session data
        del request.session['answers']
       # localStorage.clear();  # Note: This should be handled client-side

        return render(request, 'results.html', {
            'score': score,
            'total_questions': total_questions,
            'current_language': language,
            'user': user
        })

    # Pass initial time for display (client handles countdown)
    initial_time = 3600  # Static for JS to calculate from startTime

    if 'timer_reset' in request.GET:
        request.session['answers'] = {}
        # localStorage.clear() should be handled in JS on reset

    return render(request, 'index.html', {
        'question': question,
        'current_language': language,
        'user': user,
        'current_question': current_question,
        'total_questions': total_questions,
        'initial_time': initial_time,
        'answers': request.session.get('answers', {})
    })

@require_POST
@login_required
def save_answer(request):
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        answer = request.POST.get('answer')
        if question_id and answer:
            request.session['answers'][f'answer_{question_id}'] = answer
            request.session.modified = True
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)