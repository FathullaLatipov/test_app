# quiz/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Student


class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Пароль")

    class Meta:
        model = Student
        fields = ["first_name", "last_name", "middle_name", "password"]

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if not first_name:
            raise forms.ValidationError("Имя обязательно для заполнения.")
        return first_name
# class StudentRegistrationForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput)
#     class Meta:
#         model = Student
#         fields = ['first_name', 'last_name', 'patronymic_name', 'password']
#
# class StudentLoginForm(AuthenticationForm):
#     username = forms.CharField(label='Имя', widget=forms.TextInput(attrs={'autofocus': True}))
#     password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
#




class ExcelImportForm(forms.ModelForm):
    excel_file = forms.FileField(label="Загрузите Excel-файл")