# quiz/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student


class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=200, required=True, label='ФИО')

    class Meta:
        model = User
        fields = ('username', 'full_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Student.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name']
            )
        return user


class ExcelImportForm(forms.ModelForm):
    excel_file = forms.FileField(label="Загрузите Excel-файл")