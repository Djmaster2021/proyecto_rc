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
        dentista_obj = Dentista.objects.filter(user=user).first()
        if dentista_obj:
            return reverse("dentista:dashboard")

        # =======================
        # PACIENTE
        # =======================
        paciente = None
        if hasattr(user, "paciente_perfil"):
            paciente = user.paciente_perfil
        else:
            nombre = user.get_full_name() or (user.email.split("@")[0] if user.email else user.username)
            dentista_default = Dentista.objects.first()
            if dentista_default:
                paciente, _ = Paciente.objects.get_or_create(
                    user=user,
                    defaults={
                        "nombre": nombre,
                        "dentista": dentista_default,
                    },
                )

        # Si no pudimos crear paciente (no hay dentistas), mejor ir al home
        if not paciente:
            return reverse("home")

        # Redirigimos siempre al dashboard del paciente (teléfono ya se captura en el registro)
        return reverse("paciente:dashboard")


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter para logins sociales (Google).
    Reutiliza la lógica de MyAccountAdapter para decidir la redirección final.
    """

    def get_callback_url(self, request, app):
        """
        Fuerza la URL de callback a usar SITE_BASE_URL (https/ngrok) para evitar
        que allauth genere el redirect con IP privada si el request entra por ahí.
        """
        base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
        # Fallback a super si no hay base configurada
        if not base:
            return super().get_callback_url(request, app)
        path = f"/accounts/{app.provider}/login/callback/"
        return f"{base}{path}"

    def get_login_redirect_url(self, request, sociallogin):
        adapter = MyAccountAdapter()
        return adapter.get_login_redirect_url(request)
