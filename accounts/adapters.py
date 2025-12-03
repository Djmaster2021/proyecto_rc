# accounts/adapters.py

from django.conf import settings
from django.urls import reverse

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class MyAccountAdapter(DefaultAccountAdapter):
    """
    Adapter principal de allauth para manejar el flujo de redirecciones
    después de iniciar sesión o registrarse (correo/contraseña o Google).
    """

    def get_login_redirect_url(self, request):
        """
        Decide a dónde mandar al usuario después de iniciar sesión.
        """
        user = request.user

        # Si no está autenticado por alguna razón rara, usamos el default
        if not user.is_authenticated:
            return super().get_login_redirect_url(request)

        # Importamos aquí para evitar problemas de import circular
        from domain.models import Paciente, Dentista

        # =======================
        # DENTISTA
        # =======================
        if hasattr(user, "dentista"):
            return reverse("dentista:dashboard")

        # =======================
        # PACIENTE
        # =======================
        # 1) Si ya tiene perfil_paciente, lo usamos
        if hasattr(user, "paciente_perfil"):
            paciente = user.paciente_perfil
        else:
            # 2) Si NO tiene, lo creamos automáticamente
            nombre = user.get_full_name() or (user.email.split("@")[0] if user.email else user.username)
            from domain.models import Dentista
            dentista_default = Dentista.objects.first()
            if dentista_default is None:
                # No hay dentista registrado; mandamos al home con mensaje genérico
                return reverse("home")
            paciente, _ = Paciente.objects.get_or_create(
                user=user,
                defaults={
                    "nombre": nombre,
                    "dentista": dentista_default,
                },
            )

        # Ahora estamos seguros de que "paciente" existe

        telefono = (paciente.telefono or "").strip()

        # Si NO tiene teléfono, lo mandamos primero a completar el perfil
        if not telefono:
            return reverse("paciente:completar_perfil")

        # Si ya tiene teléfono, directo al dashboard del paciente
        return reverse("paciente:dashboard")


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter para logins sociales (Google).
    Reutiliza la lógica de MyAccountAdapter para decidir la redirección final.
    """

    def get_login_redirect_url(self, request, sociallogin):
        adapter = MyAccountAdapter()
        return adapter.get_login_redirect_url(request)
