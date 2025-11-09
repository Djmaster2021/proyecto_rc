# paciente/services.py
from datetime import datetime, timedelta, date
from domain.models import Cita, Disponibilidad

def obtener_horarios_disponibles(fecha_str, duracion_minutos):
    """
    Calcula los bloques de tiempo disponibles para una fecha específica
    y una duración de servicio determinada.
    """
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return []

    # 1. Obtener el día de la semana (0=Lunes, 6=Domingo)
    dia_semana = fecha.weekday()

    # 2. Buscar el horario laboral del dentista para ese día
    # NOTA: Asumimos un solo dentista principal por ahora para simplificar.
    # En un futuro multi-dentista, filtraríamos por dentista_id también.
    disponibilidad = Disponibilidad.objects.filter(dia_semana=dia_semana).first()

    if not disponibilidad:
        return []  # No trabaja este día

    # 3. Definir inicio y fin de la jornada laboral
    inicio_jornada = datetime.combine(fecha, disponibilidad.hora_inicio)
    fin_jornada = datetime.combine(fecha, disponibilidad.hora_fin)

    # 4. Obtener todas las citas confirmadas o pendientes de ese día
    citas_existentes = Cita.objects.filter(
        fecha_hora_inicio__date=fecha,
        estado__in=[Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.CONFIRMADA]
    ).order_by('fecha_hora_inicio')

    # 5. Algoritmo de búsqueda de huecos
    horarios_libres = []
    tiempo_actual = inicio_jornada
    duracion_delta = timedelta(minutes=int(duracion_minutos))

    for cita in citas_existentes:
        # Verificar si cabe una cita antes de la siguiente ya agendada
        inicio_cita = cita.fecha_hora_inicio.replace(tzinfo=None) # Quitamos zona horaria para comparar fácil
        
        while tiempo_actual + duracion_delta <= inicio_cita:
            horarios_libres.append(tiempo_actual.strftime("%H:%M"))
            tiempo_actual += timedelta(minutes=30) # Saltos de 30 mins para ofrecer opciones

        # Saltamos el tiempo ocupado por la cita actual
        tiempo_actual = max(tiempo_actual, cita.fecha_hora_fin.replace(tzinfo=None))

    # Verificar huecos después de la última cita hasta el fin de la jornada
    while tiempo_actual + duracion_delta <= fin_jornada:
        horarios_libres.append(tiempo_actual.strftime("%H:%M"))
        tiempo_actual += timedelta(minutes=30)

    return horarios_libres