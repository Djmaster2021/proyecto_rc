from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site

try:
    from allauth.socialaccount.models import SocialApp
except Exception as exc:  # pragma: no cover
    raise CommandError(f"No se pudo importar SocialApp: {exc}")


class Command(BaseCommand):
    help = "Crea/actualiza la app de Google OAuth (allauth) usando variables de entorno."

    def add_arguments(self, parser):
        parser.add_argument(
            "--site-id",
            type=int,
            default=getattr(settings, "SITE_ID", 1),
            help="ID del Site a asociar (default: settings.SITE_ID o 1).",
        )

    def handle(self, *args, **options):
        import os

        client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", None) or os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", None) or os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise CommandError(
                "Define GOOGLE_OAUTH_CLIENT_ID y GOOGLE_OAUTH_CLIENT_SECRET en el entorno antes de correr este comando."
            )

        site_id = options["site_id"]
        try:
            site = Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            raise CommandError(f"Site con id={site_id} no encontrado. Revisa la tabla django_site.")

        app, created = SocialApp.objects.update_or_create(
            provider="google",
            defaults={"name": "Google OAuth", "client_id": client_id, "secret": client_secret},
        )
        app.sites.set([site])
        app.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"SocialApp Google creada y ligada al Site {site.domain} (id {site.id})."))
        else:
            self.stdout.write(self.style.SUCCESS(f"SocialApp Google actualizada y ligada al Site {site.domain} (id {site.id})."))
