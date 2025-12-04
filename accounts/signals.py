from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from domain.models import Dentista, Paciente


@receiver(pre_delete, sender=User)
def borrar_perfiles_relacionados(sender, instance, **kwargs):
    """
    Evita errores de FK al borrar usuarios desde el admin eliminando
    perfiles dependientes que usan restricciones estrictas en la BD.
    """
    try:
        if hasattr(instance, "dentista"):
            instance.dentista.delete()
    except Exception as exc:
        print(f"[WARN] No se pudo borrar perfil de dentista antes de eliminar usuario {instance.id}: {exc}")

    try:
        if hasattr(instance, "paciente_perfil"):
            # Se elimina solo si el perfil está enlazado explícitamente
            instance.paciente_perfil.delete()
    except Exception as exc:
        print(f"[WARN] No se pudo borrar perfil de paciente antes de eliminar usuario {instance.id}: {exc}")
