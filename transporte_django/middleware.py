from django.shortcuts import redirect
from django.conf import settings

# URLs que ficam abertas sem login (login, logout, admin, webhook WhatsApp, API token)
URLS_PUBLICAS = [
	'/static/',
	'/media/',
    '/login/',
    '/logout/',
    '/admin/',
    '/api/whatsapp/webhook/',
    '/api/token/',
    '/api/token/refresh/',
]

class LoginObrigatorioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        # Permite URLs públicas
        for url in URLS_PUBLICAS:
            if path.startswith(url):
                return self.get_response(request)
        # Se não autenticado, redireciona para login
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={path}")
        return self.get_response(request)
