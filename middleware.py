from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve


class LoginRequiredMiddleware:
    """
    Middleware que exige login em todas as páginas, exceto login, logout e admin.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que não exigem login
        excluded_urls = [
            settings.LOGIN_URL.lstrip("/"),
            "logout/",
            "admin/login/",
            "admin/logout/",
            "admin/password_change/",
            "admin/password_change/done/",
        ]
        path = request.path_info.lstrip("/")
        if not request.user.is_authenticated and not any(
            path.startswith(url) for url in excluded_urls
        ):
            return redirect(settings.LOGIN_URL + f"?next={request.path}")
        return self.get_response(request)
