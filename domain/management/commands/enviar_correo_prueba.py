from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Envía un correo de prueba para validar configuración SMTP."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to_email",
            help="Correo destino. Por defecto usa EMAIL_HOST_USER.",
        )
        parser.add_argument(
            "--subject",
            dest="subject",
            default="Prueba SMTP – Consultorio RC",
            help="Asunto opcional.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Ignora SEND_EMAILS=False y envía de todas formas.",
        )

    def handle(self, *args, **options):
        remitente = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(
            settings, "EMAIL_HOST_USER", None
        )
        if not remitente:
            raise CommandError("No hay remitente configurado (DEFAULT_FROM_EMAIL o EMAIL_HOST_USER).")

        destinatario = options.get("to_email") or getattr(settings, "EMAIL_HOST_USER", None)
        if not destinatario:
            raise CommandError("Proporciona --to o configura EMAIL_HOST_USER.")

        if not getattr(settings, "SEND_EMAILS", True) and not options.get("force"):
            self.stdout.write(self.style.WARNING("SEND_EMAILS=False; correo no enviado. Usa --force para probar."))
            return

        asunto = options["subject"]
        mensaje = (
            "Correo de prueba del sistema RC Dental.\n\n"
            "Si lo recibes, la configuración SMTP es correcta.\n"
            "Este mensaje fue enviado desde la gestión de comandos de Django."
        )

        send_mail(
            asunto,
            mensaje,
            remitente,
            [destinatario],
            fail_silently=False,
        )

        self.stdout.write(self.style.SUCCESS(f"Correo de prueba enviado a {destinatario}"))
