# paciente/context_processors.py

from domain.models import Paciente
from domain.ai_services import calcular_penalizacion_paciente


def penalizacion_paciente(request):
    """
    Inyecta en el contexto info de penalización SOLO para pacientes
    válidos y guardados en BD.
    """
    # Si no está logueado, no hacemos nada
    if not request.user.is_authenticated:
        return {}

    # Intentar obtener el perfil Paciente
    try:
        perfil_paciente = Paciente.objects.get(user=request.user)
    except Paciente.DoesNotExist:
        # Usuario sin perfil paciente (admin, dentista, primera vez con Google, etc.)
        return {}

    # Si por alguna razón el perfil no está guardado aún
    if not perfil_paciente.pk:
        return {}

    info = calcular_penalizacion_paciente(perfil_paciente)

    # Exponemos con dos llaves para compatibilidad
    return {
        "penalizacion_paciente": info,
        "penalizacion_info": info,
    }
