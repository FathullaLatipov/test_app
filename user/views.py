from django.shortcuts import render
from .models import Question
from django.core.paginator import Paginator

def quiz_list(request):
    language = request.GET.get('lang', 'uz')
    questions = Question.objects.filter(language=language).prefetch_related('choices')
    return render(request, 'index.html', {
        'questions': questions,
        'current_language': language
    })