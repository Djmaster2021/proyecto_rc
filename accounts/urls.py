# accounts/urls.py
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

app_name = "accounts"

urlpatterns = [
    # Dashboard / índice de accounts
    path("", getattr(views, "index", TemplateView.as_view(template_name="accounts/base.html")), name="index"),

    # Registro / login / logout (si tienes vistas custom, se usan, si no se usan templates)
    path("register/", getattr(views, "register", TemplateView.as_view(template_name="accounts/register.html")), name="register"),
    path("login/", getattr(views, "login_view", TemplateView.as_view(template_name="accounts/login.html")), name="login"),
    path("logout/", getattr(views, "logout_view", TemplateView.as_view(template_name="accounts/base.html")), name="logout"),

    # Incluir las rutas provistas por django.contrib.auth (login, logout, password reset, etc.)
    path("", include("django.contrib.auth.urls")),
]
