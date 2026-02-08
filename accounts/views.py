# accounts/views.py

from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, PasswordResetView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.conf import settings
from django.http import HttpResponseRedirect

from .forms import (
    PacienteRegisterForm,
    DentistaRegisterForm,
    UsernameOrEmailAuthenticationForm,
    UsernameOrEmailPasswordResetForm,
)


# ==============================
# FUNCIÓN ÚNICA DE REDIRECCIÓN
# ==============================

def redirect_by_role(request):
    """
    Después de cualquier login (normal o Google), enviamos
    al usuario al panel correcto según su rol.
    """
    user = request.user

    if not user.is_authenticated:
        # Nombre de la URL de login (definida en urls.py como account_login)
        return redirect("account_login")

    from domain.models import Dentista, Paciente
    dentista_obj = Dentista.objects.filter(user=user).first()
    tiene_dentista = dentista_obj is not None
    tiene_paciente = Paciente.objects.filter(user=user).exists()

    # 1. Admin / staff -> panel de Django
    if user.is_superuser or user.is_staff or user.groups.filter(name="Administrador").exists():
        return redirect("/admin/")

    # 2. Dentista -> dashboard dentista (solo si existe perfil)
    if dentista_obj:
        return redirect("dentista:dashboard")

    # 3. Paciente -> dashboard paciente (por defecto)
    if not tiene_paciente:
        dentista_default = Dentista.objects.first()
        if dentista_default:
            nombre_base = user.get_full_name() or user.username or "Paciente"
            nombre = nombre_base
            if Paciente.objects.filter(dentista=dentista_default, nombre=nombre).exists():
                suffix = user.username or user.email or str(user.pk)
                nombre = f"{nombre_base} ({suffix})"
                i = 2
                while Paciente.objects.filter(dentista=dentista_default, nombre=nombre).exists():
                    nombre = f"{nombre_base} ({suffix}-{i})"
                    i += 1
            try:
                Paciente.objects.create(user=user, dentista=dentista_default, nombre=nombre)
            except IntegrityError:
                # Si hay colision concurrente, evitamos romper el login.
                pass
    return redirect("paciente:dashboard")


# ==============================
# LOGIN CON USUARIO / CONTRASEÑA
# ==============================

class CustomLoginView(LoginView):
    """
    Login con usuario/contraseña usando template accounts/login.html.
    Después del login, redirige por rol usando redirect_by_role.
    """
    template_name = "accounts/login.html"
    authentication_form = UsernameOrEmailAuthenticationForm

    def get_success_url(self):
        # Mandamos siempre a la vista central de redirección
        return reverse("accounts:redirect_by_role")

    def form_invalid(self, form):
        messages.error(self.request, "Usuario o contraseña incorrectos. Intenta de nuevo.")
        return super().form_invalid(form)


class CustomPasswordResetView(PasswordResetView):
    """
    Password reset con logs sencillos y from_email explícito.
    """
    template_name = "accounts/password_reset_form.html"
    form_class = UsernameOrEmailPasswordResetForm
    email_template_name = "accounts/password_reset_email.html"
    html_email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = "/accounts/password_reset/done/"

    def get_from_email(self):
        return settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER

    def form_valid(self, form):
        if not getattr(settings, "SEND_EMAILS", True):
            print("[PASSWORD RESET] SEND_EMAILS=False; no se envió correo.")
        try:
            email_destino = form.cleaned_data.get("email")
            # Enviamos usando el backend configurado
            form.save(
                domain_override=self.request.get_host(),
                use_https=self.request.is_secure(),
                token_generator=self.token_generator,
                subject_template_name=self.subject_template_name,
                email_template_name=self.email_template_name,
                html_email_template_name=self.html_email_template_name,
                from_email=self.get_from_email(),
                request=self.request,
            )
            # Log de destinatario y enlaces generados (para depurar entregabilidad)
            base = (
                settings.SITE_BASE_URL.rstrip("/")
                if hasattr(settings, "SITE_BASE_URL")
                else f"{'https' if self.request.is_secure() else 'http'}://{self.request.get_host()}"
            )
            users = list(form.get_users(email_destino))
            if not users:
                print(f"[PASSWORD RESET] No hay usuarios con email/usuario: {email_destino}")
            for user in users:
                # No registrar enlaces ni tokens de recuperación en logs.
                print(f"[PASSWORD RESET] Link emitido para usuario: {user.get_username()}")

            print(f"[PASSWORD RESET] Intento de envío a: {email_destino} (usuarios encontrados: {len(users)})")
            return HttpResponseRedirect(self.success_url)
        except Exception as exc:
            messages.error(self.request, "No pudimos enviar el correo. Intenta de nuevo en unos minutos.")
            print(f"[PASSWORD RESET] Error enviando correo: {exc}")
            return self.form_invalid(form)


# ==============================
# REGISTRO DE PACIENTES
# ==============================

def register(request):
    """
    Registro de pacientes (self-service).
    """
    FormClass = PacienteRegisterForm

    if request.method == "POST":
        form = FormClass(request.POST)
        if form.is_valid():
            user = form.save()

            messages.success(
                request,
                "Tu cuenta ha sido creada correctamente. ¡Bienvenido!",
            )

            # Login directo y redirección al dashboard paciente
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("paciente:dashboard")
    else:
        form = FormClass()

    return render(request, "accounts/register.html", {"form": form})


# Nota: post_login queda obsoleto; redirect_by_role cubre los flujos.
