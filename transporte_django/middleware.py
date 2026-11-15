from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import logout
from django.utils import timezone

# URLs que ficam abertas sem login (login, logout, admin, webhook WhatsApp, API token)
URLS_PUBLICAS = [
    "/static/",
    "/media/",
    "/login/",
    "/logout/",
    settings.ADMIN_URL_PATH,
    "/api/whatsapp/webhook/",
    "/api/token/",
    "/api/token/refresh/",
]


class AdminIPAllowlistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_path = settings.ADMIN_URL_PATH
        allowed_ips = getattr(settings, "ADMIN_ALLOWED_IPS", [])

        if request.path_info.startswith(admin_path) and allowed_ips:
            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            client_ip = (
                forwarded_for.split(",")[0].strip()
                if forwarded_for
                else request.META.get("REMOTE_ADDR", "").strip()
            )
            if client_ip not in allowed_ips:
                return HttpResponseForbidden("Acesso ao admin bloqueado para este IP.")

        return self.get_response(request)


class LoginObrigatorioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if path.startswith("/static/") or path.startswith("/media/"):
            return self.get_response(request)

        if path.startswith("/login/") or path.startswith("/logout/"):
            return self.get_response(request)

        if path.startswith(settings.ADMIN_URL_PATH):
            return self.get_response(request)

        if path.startswith("/api/whatsapp/webhook/"):
            return self.get_response(request)

        if path.startswith("/api/token/"):
            return self.get_response(request)

        if not request.user.is_authenticated:
            if path.startswith("/api/"):
                return JsonResponse(
                    {"sucesso": False, "erro": "nao_autenticado"}, status=401
                )
            return redirect(f"{settings.LOGIN_URL}?next={path}")

        timeout = int(getattr(settings, "IDLE_LOGOUT_SECONDS", 0) or 0)
        if timeout > 0:
            now_ts = int(timezone.now().timestamp())
            last_activity = request.session.get("_last_activity_ts")
            if last_activity and now_ts - int(last_activity) > timeout:
                logout(request)
                request.session.flush()
                if path.startswith("/api/"):
                    return JsonResponse(
                        {"sucesso": False, "erro": "sessao_expirada"}, status=401
                    )
                return redirect(f"{settings.LOGIN_URL}?next={path}")
            request.session["_last_activity_ts"] = now_ts

        return self.get_response(request)
