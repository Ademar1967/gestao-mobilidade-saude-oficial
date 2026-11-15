"""
URL configuration for transporte_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


class TokenObtainPairThrottledView(TokenObtainPairView):
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "token_obtain"


class TokenRefreshThrottledView(TokenRefreshView):
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "token_refresh"

urlpatterns = [
    # Admin isolado por caminho configurável em settings.ADMIN_URL_PATH
    path(settings.ADMIN_URL_PATH.lstrip("/"), admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("polls.urls")),
    path("api/", include("polls.api_urls")),
    path("api/token/", TokenObtainPairThrottledView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshThrottledView.as_view(), name="token_refresh"),
]
