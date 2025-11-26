from datetime import datetime, timedelta
from domain.models import Cita, Disponibilidad, Dentista

def obtener_horarios_disponibles(fecha_str, duracion_minutos):
    """
    Calcula con precisión milimétrica los huecos disponibles.
    Respeta:
    1. Turnos partidos (ej. comida).
    2. Citas ya existentes (no empalma).
    3. Duración del servicio (no ofrece huecos donde no cabe).
    """
    try:
        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return []

    dia_semana = fecha_obj.weekday()

    # 1. OBTENER TURNOS DEL DÍA
    # Si hay múltiples dentistas en el futuro, aquí filtraríamos por dentista también.
    # Por ahora tomamos todos los turnos activos para ese día de la semana.
    turnos = Disponibilidad.objects.filter(dia_semana=dia_semana).order_by('hora_inicio')
    
    if not turnos.exists():
        return [] # Día libre completo (ej. Domingo)

    # 2. OBTENER CITAS YA AGENDADAS PARA ESE DÍA
    # Solo nos importan las que están ocupando un espacio real (Pendientes o Confirmadas)
    citas_existentes = Cita.objects.filter(
        fecha_hora_inicio__date=fecha_obj,
        estado__in=[Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.CONFIRMADA]
    ).order_by('fecha_hora_inicio')

    horarios_libres = []
    duracion_delta = timedelta(minutes=int(duracion_minutos))
    paso_agenda = timedelta(minutes=30) # Intervalos de 30 min para ofrecer opciones

    # 3. ANALIZAR CADA TURNO (La magia ocurre aquí)
    for turno in turnos:
        # Definimos el inicio y fin exacto de ESTE turno (ej. 7:00 a 13:00)
        inicio_turno = datetime.combine(fecha_obj, turno.hora_inicio)
        fin_turno = datetime.combine(fecha_obj, turno.hora_fin)

        tiempo_actual = inicio_turno

        # Mientras el servicio quepa antes de que termine el turno...
        while tiempo_actual + duracion_delta <= fin_turno:
            hora_fin_propuesta = tiempo_actual + duracion_delta
            
            # Verificamos si choca con alguna cita YA EXISTENTE
            ocupado = False
            for cita in citas_existentes:
                # Convertimos a 'naive' (sin zona horaria) para comparar fácil
                inicio_cita = cita.fecha_hora_inicio.replace(tzinfo=None)
                fin_cita = cita.fecha_hora_fin.replace(tzinfo=None)

                # Lógica de colisión: Si el hueco propuesto se solapa con la cita
                if (tiempo_actual < fin_cita) and (hora_fin_propuesta > inicio_cita):
                    ocupado = True
                    # Truco PRO: Si está ocupado, saltamos directamente al final de esa cita
                    # para no perder tiempo revisando minutos intermedios que ya sabemos que están ocupados.
                    tiempo_actual = max(tiempo_actual, fin_cita)
                    # Redondeamos al siguiente intervalo de 30 min si es necesario
                    # (Opcional, pero mantiene la agenda ordenada)
                    break # Salimos del bucle de citas, ya encontramos un choque
            
            if not ocupado:
                # ¡Hueco encontrado! Lo agregamos a la lista para el paciente
                horarios_libres.append(tiempo_actual.strftime("%H:%M"))
                # Avanzamos al siguiente slot posible
                tiempo_actual += paso_agenda

    # Limpiamos duplicados y ordenamos por si acaso
    return sorted(list(set(horarios_libres)))