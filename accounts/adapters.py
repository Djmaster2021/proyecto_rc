# accounts/adapters.py

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import Group
from django.urls import reverse

from domain.models import Paciente as PacientePerfil


class RoleRedirectMixin:
    """
    Mixin para redirigir después de login según rol.
    Lo usan tanto el login normal como el social (Google).
    """

    def get_login_redirect_url(self, request):
        user = request.user

        if not user or not user.is_authenticated:
            return super().get_login_redirect_url(request)

        # Admin / staff -> panel de Django
        if user.is_superuser or user.is_staff or user.groups.filter(name="Administrador").exists():
            return reverse("admin:index")

        # Dentista -> dashboard dentista
        if user.groups.filter(name="Dentista").exists():
            return reverse("dentista:dashboard")

        # Paciente -> dashboard paciente
        if user.groups.filter(name="Paciente").exists():
            return reverse("paciente:dashboard")

        # Fallback -> home
        return "/"


class MyAccountAdapter(RoleRedirectMixin, DefaultAccountAdapter):
    """
    Adapter para registro/login normal (usuario/contraseña).
    """

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=commit)
        self._assign_paciente_role(user)
        self._create_paciente_profile(user)
        return user

    # Helpers compartidos
    def _assign_paciente_role(self, user):
        grupo, _ = Group.objects.get_or_create(name="Paciente")
        user.groups.add(grupo)

    def _create_paciente_profile(self, user):
        # Crea el registro en domain.Paciente si no existe
        PacientePerfil.objects.get_or_create(user=user)


class MySocialAccountAdapter(RoleRedirectMixin, DefaultSocialAccountAdapter):
    """
    Adapter para login con Google (social).
    """

    def save_user(self, request, sociallogin, form=None):
        # Deja que allauth cree el user primero
        user = super().save_user(request, sociallogin, form=form)

        # Aseguramos rol y perfil de Paciente
        self._assign_paciente_role(user)
        self._create_paciente_profile(user)

        return user

    # Mismos helpers que arriba
    def _assign_paciente_role(self, user):
        grupo, _ = Group.objects.get_or_create(name="Paciente")
        user.groups.add(grupo)

    def _create_paciente_profile(self, user):
        PacientePerfil.objects.get_or_create(user=user)
