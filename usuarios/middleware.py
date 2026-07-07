from django.contrib.auth.views import redirect_to_login
from django.conf import settings

CAMINHOS_PUBLICOS = (
    '/usuarios/login/',
    '/admin/',
    settings.STATIC_URL,
    settings.MEDIA_URL,
)


class LoginObrigatorioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.path.startswith(CAMINHOS_PUBLICOS):
            return redirect_to_login(request.get_full_path(), login_url=settings.LOGIN_URL)
        return self.get_response(request)
