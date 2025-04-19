from django.utils import translation

class ForceAdminLocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Применить русский язык только для URL'ов, начинающихся с /admin/
        if request.path.startswith('/admin/'):
            translation.activate('ru')
            request.LANGUAGE_CODE = 'ru'
        return self.get_response(request)
