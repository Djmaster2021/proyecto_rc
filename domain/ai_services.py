from django.utils import timezone
from .models import Cita

def calcular_score_riesgo(paciente):
    """
    IA BÁSICA: Algoritmo de cálculo de riesgo basado en historial.
    Retorna un valor flotante entre 0.0 (Santo) y 1.0 (Diablo).
    """
    # 1. Obtener historial relevante
    total_citas = Cita.objects.filter(paciente=paciente).count()
    
    # Si es nuevo, le damos el beneficio de la duda (Riesgo bajo)
    if total_citas < 2:
        paciente.score_riesgo = 0.0
        paciente.save()
        return 0.0

    # 2. Contar "pecados" (Inasistencias)
    faltas = Cita.objects.filter(
        paciente=paciente,
        estado=Cita.EstadoCita.NO_SHOW
    ).count()

    # 3. Algoritmo de Riesgo (Regla de Tres Simple Ajustada)
    # - 0 faltas = 0.0
    # - 1 falta = 0.4 (Alerta Amarilla)
    # - 2 faltas = 0.7 (Alerta Naranja)
    # - 3+ faltas = 1.0 (Alerta Roja - Suspensión inminente)
    
    if faltas == 0:
        nuevo_score = 0.0
    elif faltas == 1:
        nuevo_score = 0.4
    elif faltas == 2:
        nuevo_score = 0.7
    else:
        nuevo_score = 1.0

    # 4. Guardar el nuevo score en el perfil del paciente
    paciente.score_riesgo = nuevo_score
    paciente.save()
    
    return nuevo_score

def obtener_nivel_riesgo(score):
    """Convierte el score numérico en una etiqueta legible y un color."""
    if score >= 0.8:
        return "ALTO", "danger"    # Rojo
    elif score >= 0.4:
        return "MEDIO", "warning"  # Amarillo
    else:
        return "BAJO", "success"   # Verde