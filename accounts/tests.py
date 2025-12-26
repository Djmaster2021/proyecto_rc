import os
from unittest import mock

from allauth.socialaccount.models import SocialApp
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from domain.models import Dentista, Paciente


class SetupGoogleSocialAppTests(TestCase):
    def test_command_requires_credentials(self):
        with override_settings(GOOGLE_OAUTH_CLIENT_ID=None, GOOGLE_OAUTH_CLIENT_SECRET=None):
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(CommandError):
                    call_command("setup_google_socialapp")

    def test_command_creates_socialapp(self):
        site = Site.objects.get_current()
        with override_settings(GOOGLE_OAUTH_CLIENT_ID="id-test", GOOGLE_OAUTH_CLIENT_SECRET="secret-test"):
            call_command("setup_google_socialapp", site_id=site.id)

        app = SocialApp.objects.get(provider="google")
        self.assertEqual(app.client_id, "id-test")
        self.assertEqual(app.secret, "secret-test")
        self.assertEqual(list(app.sites.all()), [site])


class LoginRedirectTests(TestCase):
    def test_redirects_dentista(self):
        user = User.objects.create_user(username="dent", password="pass")
        Dentista.objects.create(user=user, nombre="Dr. Test")
        self.client.force_login(user)

        response = self.client.get(reverse("redireccionar_usuario"))
        self.assertRedirects(response, reverse("dentista:dashboard"), fetch_redirect_response=False)

    def test_redirects_paciente(self):
        dentista_user = User.objects.create_user(username="doc", password="pass")
        dentista = Dentista.objects.create(user=dentista_user, nombre="Dr. Paciente")
        user = User.objects.create_user(username="pac", password="pass")
        Paciente.objects.create(user=user, dentista=dentista, nombre="Paciente Test")
        self.client.force_login(user)

        response = self.client.get(reverse("redireccionar_usuario"))
        self.assertRedirects(response, reverse("paciente:dashboard"), fetch_redirect_response=False)

    def test_redirects_new_user_to_completar_perfil(self):
        user = User.objects.create_user(username="nuevo", password="pass")
        self.client.force_login(user)

        response = self.client.get(reverse("redireccionar_usuario"))
        self.assertRedirects(response, reverse("paciente:completar_perfil"), fetch_redirect_response=False)
