import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from domain.models import Dentista


class Command(BaseCommand):
    help = "Crea un dentista por defecto si no existe ninguno (usuario + perfil)."

    def handle(self, *args, **options):
        if Dentista.objects.exists():
            self.stdout.write(self.style.SUCCESS("Ya existe al menos un dentista. No se hicieron cambios."))
            return

        nombre = os.getenv("DEFAULT_DENTISTA_NAME", "Dentista Principal")
        email = os.getenv("DEFAULT_DENTISTA_EMAIL", "dentista@example.com")
        password = os.getenv("DEFAULT_DENTISTA_PASSWORD", "Dentista123!")
        username = os.getenv("DEFAULT_DENTISTA_USERNAME", email.split("@")[0])

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": nombre,
            },
        )
        if created:
            user.set_password(password)
            # Permite que administre en el panel /admin si se desea
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.NOTICE(f"Usuario creado: {username} / {email}"))
        else:
            self.stdout.write(self.style.WARNING(f"Usuario {username} ya existía; se usará para el perfil."))

        dentista, dentista_created = Dentista.objects.get_or_create(
            user=user,
            defaults={
                "nombre": f"Dr. {nombre}".strip(),
                "telefono": "",
                "especialidad": "Odontología General",
            },
        )

        if dentista_created:
            self.stdout.write(self.style.SUCCESS("Dentista por defecto creado correctamente."))
        else:
            self.stdout.write(self.style.SUCCESS("Ya había un perfil de dentista para ese usuario."))
