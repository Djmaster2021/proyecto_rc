from django.utils import timezone
from .models import Cita, Paciente

def calcular_score_riesgo(paciente):
    """
    IA BÁSICA: Algoritmo de cálculo de riesgo basado en historial.
    Retorna un valor flotante entre 0.0 (Bajo) y 1.0 (Alto).
    """
    # 1. Obtener historial relevante
    total_citas = Cita.objects.filter(paciente=paciente).count()
    
    if total_citas < 2:
        paciente.score_riesgo = 0.0
        paciente.save()
        return 0.0

    # 2. Contar faltas
    faltas = Cita.objects.filter(
        paciente=paciente,
        estado=Cita.EstadoCita.NO_SHOW
    ).count()

    # 3. Algoritmo de Riesgo
    if faltas == 0: nuevo_score = 0.0
    elif faltas == 1: nuevo_score = 0.4
    elif faltas == 2: nuevo_score = 0.7
    else: nuevo_score = 1.0 # 3+ faltas

    paciente.score_riesgo = nuevo_score
    paciente.save()
    
    return nuevo_score

def procesar_inasistencia(cita):
    """
    Lógica central para manejar una falta (NO_SHOW):
    1. Marca la cita como NO_SHOW.
    2. Recalcula el score de riesgo (IA).
    3. Aplica strikes y suspende si es necesario.
    Retorna un mensaje de resultado.
    """
    paciente = cita.paciente
    mensaje_resultado = f"Inasistencia registrada para {paciente.nombre}."

    # Solo penalizamos si el paciente había prometido ir
    if cita.estado in [Cita.EstadoCita.CONFIRMADA, Cita.EstadoCita.CONFIRMADA_PACIENTE, Cita.EstadoCita.CONFIRMADA_DENTISTA]:
        
        # Reiniciar contador si su última cita SÍ fue completada
        ultima_cita_completada = Cita.objects.filter(
            paciente=paciente, 
            estado=Cita.EstadoCita.COMPLETADA,
            fecha_hora_inicio__lt=cita.fecha_hora_inicio
        ).order_by('-fecha_hora_inicio').first()

        if ultima_cita_completada:
             # Si esta falta es posterior a su última asistencia, se reinicia el contador
             if paciente.inasistencias_consecutivas > 0:
                 paciente.inasistencias_consecutivas = 0

        paciente.inasistencias_consecutivas += 1
        
        # REGLA DE NEGOCIO: 3 strikes = Suspensión
        if paciente.inasistencias_consecutivas >= 3:
            paciente.esta_suspendido = True
            paciente.fecha_suspension = timezone.now()
            paciente.user.is_active = False # Bloqueo de login
            paciente.user.save()
            mensaje_resultado = f"¡ALERTA! {paciente.nombre} ha sido SUSPENDIDO por 3 faltas consecutivas."
        else:
            mensaje_resultado = f"Falta registrada. Strike {paciente.inasistencias_consecutivas}/3 para {paciente.nombre}."
    
    # 1. Marcar la cita como NO_SHOW
    cita.estado = Cita.EstadoCita.NO_SHOW
    cita.save()
    
    # 2. Recalcular Score de Riesgo (IA)
    calcular_score_riesgo(paciente)
    
    # 3. Guardar cambios en el paciente (strikes/suspensión)
    paciente.save()
    
    return mensaje_resultado