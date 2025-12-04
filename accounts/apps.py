from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Importa señales para limpiar perfiles ligados antes de borrar usuarios
        from . import signals  # noqa: F401
