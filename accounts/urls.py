from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# Es importante que app_name coincida con el namespace en el urls.py principal
app_name = "accounts"

urlpatterns = [
    # 1. Login personalizado (usa la clase que definimos en views.py)
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),

    # 2. Logout (usa la vista nativa de Django)
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="accounts:login"),
        name="logout",
    ),
    
    path("post-login/", views.post_login, name="post_login"),

    # 3. Registro (usa la función register de views.py)
    path("register/", views.register, name="register"),

    # --- RECUPERACIÓN DE CONTRASEÑA ---

# 1. El formulario donde pones el correo
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html',
        html_email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/password_reset/done/'
    ), name='password_reset'),

    # 2. Mensaje de "Te hemos enviado un correo"
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),

    # 3. El enlace que llega al correo (ESTE ES EL QUE FALLABA)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ), name='password_reset_confirm'),

    # 4. Mensaje de "Contraseña cambiada con éxito"
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]