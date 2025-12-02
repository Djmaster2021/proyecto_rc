from datetime import datetime, timedelta
# Importamos Horario en lugar de Disponibilidad
from domain.models import Cita, Horario, Dentista, AvisoDentista


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

    # 1. OBTENER TURNOS DEL DÍA (Usando modelo Horario)
    turnos = Horario.objects.filter(dia_semana=dia_semana).order_by("hora_inicio")

    if not turnos.exists():
        return []  # Día libre completo (ej. Domingo)

    # 2. OBTENER CITAS YA AGENDADAS PARA ESE DÍA
    # CORRECCIÓN: Filtramos por 'fecha' directamente y usamos strings para los estados
    citas_existentes = Cita.objects.filter(
        fecha=fecha_obj,
        estado__in=['PENDIENTE', 'CONFIRMADA'],
    ).order_by("hora_inicio")

    horarios_libres = []
    duracion_delta = timedelta(minutes=int(duracion_minutos))
    paso_agenda = timedelta(minutes=30)  # Intervalos de 30 min para ofrecer opciones

    # 3. ANALIZAR CADA TURNO
    for turno in turnos:
        # Definimos el inicio y fin exacto de ESTE turno
        inicio_turno = datetime.combine(fecha_obj, turno.hora_inicio)
        fin_turno = datetime.combine(fecha_obj, turno.hora_fin)

        tiempo_actual = inicio_turno

        # Mientras el servicio quepa antes de que termine el turno...
        while tiempo_actual + duracion_delta <= fin_turno:
            hora_fin_propuesta = tiempo_actual + duracion_delta

            # Verificamos si choca con alguna cita YA EXISTENTE
            ocupado = False
            for cita in citas_existentes:
                # CORRECCIÓN: Construimos los datetimes al vuelo porque en la BD están separados
                # y nos aseguramos de que no tengan zona horaria (naive) para comparar fácil.
                inicio_cita = datetime.combine(cita.fecha, cita.hora_inicio)
                fin_cita = datetime.combine(cita.fecha, cita.hora_fin)

                # Lógica de colisión: Si el hueco propuesto se solapa con la cita
                if (tiempo_actual < fin_cita) and (hora_fin_propuesta > inicio_cita):
                    ocupado = True
                    # Truco: Si está ocupado, saltamos directamente al final de esa cita
                    tiempo_actual = max(tiempo_actual, fin_cita)
                    break  # Salimos del bucle de citas, ya encontramos un choque

            if not ocupado:
                # ¡Hueco encontrado! Lo agregamos a la lista
                horarios_libres.append(tiempo_actual.strftime("%H:%M"))
                # Avanzamos al siguiente slot posible
                tiempo_actual += paso_agenda

    # Limpiamos duplicados y ordenamos
    return sorted(list(set(horarios_libres)))


# ============================================================
# AVISOS PARA EL DENTISTA
# ============================================================

def crear_aviso_por_cita(cita, tipo, mensaje):
    """
    Crea un AvisoDentista asociado a una cita y a su dentista.
    """
    if cita is None or cita.dentista is None:
        return None

    try:
        aviso = AvisoDentista.objects.create(
            dentista=cita.dentista,
            cita=cita,
            tipo=tipo,
            mensaje=mensaje,
        )
        return aviso
    except Exception:
        return None