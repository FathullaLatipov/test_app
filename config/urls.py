from django.contrib import admin
from django.urls import path
from tests.views import HomeView
from user.views import quiz_list, register_student, student_logout, student_login, save_answer, verify_unique_code, set_timer, download_student_report
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', quiz_list, name='home'),
    path("register/", register_student, name="register"),
    path("login/", student_login, name="login"),
    path('logout/', student_logout, name='logout'),
    path('save-answer/', save_answer, name='save_answer'),
    path('set_timer/', set_timer, name='set_timer'),
    path('verify/', verify_unique_code, name='verify_unique_code'),
    path('download_student_report/', download_student_report, name='download_student_report'),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)