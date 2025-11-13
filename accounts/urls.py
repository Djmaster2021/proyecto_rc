from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # Importa las vistas de accounts/views.py

app_name = "accounts"

urlpatterns = [
    # Vistas de Login, Logout y Register
    path("login/", views.LoginAndRedirectView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),

    # --- NUEVA RUTA: SEMÁFORO DE REDIRECCIÓN ---
    # Esta ruta recibe al usuario después de login (Google o normal) y lo manda a su sitio
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    # -------------------------------------------

    # Vistas de Reseteo de Contraseña
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html"
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]