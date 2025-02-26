from django.contrib.auth.backends import BaseBackend
from .models import Student

class StudentAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Ищем всех пользователей с таким first_name
        students = Student.objects.filter(first_name=username)
        if not students.exists():
            return None
        # Проверяем пароль у каждого, возвращаем первого подходящего
        for student in students:
            if student.check_password(password):
                return student
        return None

    def get_user(self, user_id):
        try:
            return Student.objects.get(pk=user_id)
        except Student.DoesNotExist:
            return None