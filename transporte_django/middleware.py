from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden

# URLs que ficam abertas sem login (login, logout, admin, webhook WhatsApp, API token)
URLS_PUBLICAS = [
	'/static/',
	'/media/',
    '/login/',
    '/logout/',
    settings.ADMIN_URL_PATH,
    '/api/whatsapp/webhook/',
    '/api/token/',
    '/api/token/refresh/',
    '/autocomplete_endereco_unidade/',
]


class AdminIPAllowlistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_path = settings.ADMIN_URL_PATH
        allowed_ips = getattr(settings, 'ADMIN_ALLOWED_IPS', [])

        if request.path_info.startswith(admin_path) and allowed_ips:
            forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
            client_ip = forwarded_for.split(',')[0].strip() if forwarded_for else request.META.get('REMOTE_ADDR', '').strip()
            if client_ip not in allowed_ips:
                return HttpResponseForbidden('Acesso ao admin bloqueado para este IP.')

        return self.get_response(request)

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
