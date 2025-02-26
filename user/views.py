from django.shortcuts import render, redirect
from .models import Question
from django.contrib.auth.models import User
from django.contrib.auth import login
from .forms import StudentRegistrationForm
from django.core.paginator import Paginator
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required

# def register(request):
#     if request.method == 'POST':
#         form = StudentRegistrationForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.set_password(form.cleaned_data['password'])
#             user.save()
#             print(f"✅ Успешная регистрация: {user.first_name}, пароль: {form.cleaned_data['password']}")
#             return redirect('login')
#         else:
#             print(f"❌ Ошибка валидации регистрации: {form.errors}")
#     else:
#         form = StudentRegistrationForm()
#     return render(request, 'register.html', {'form': form})
#
# def student_login(request):
#     if request.method == 'POST':
#         form = StudentLoginForm(data=request.POST)
#         if form.is_valid():
#             first_name = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             print(f"🔍 Попытка входа: first_name={first_name}, password={password}")
#             user = authenticate(request, username=first_name, password=password)
#             if user is not None:
#                 print(f"✅ Успешный вход: {user.first_name}")
#                 login(request, user)
#                 return redirect('home')
#             else:
#                 print("❌ Ошибка: Неверные учетные данные")
#                 form.add_error(None, "Пожалуйста, введите правильные имя пользователя и пароль.")
#         else:
#             print(f"❌ Ошибка валидации формы входа: {form.errors}")
#     else:
#         form = StudentLoginForm()
#     return render(request, 'login.html', {'form': form})
#
#

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
    return render(request, 'index.html', {
        'questions': questions,
        'current_language': language,
        'user': request.user
    })