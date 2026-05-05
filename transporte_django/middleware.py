from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse

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
    '/autocomplete_endereco_unidade/',
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

        if not request.user.is_authenticated:
            # Para endpoints de API, retorna JSON 401 em vez de HTML de login.
            # Isso evita quebrar autocomplete que espera resposta JSON.
            if path.startswith('/api/'):
                return JsonResponse({'sucesso': False, 'erro': 'nao_autenticado'}, status=401)
            return redirect(f"{settings.LOGIN_URL}?next={path}")

        return self.get_response(request)
