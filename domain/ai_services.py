# domain/ai_services.py

from datetime import datetime, time, timedelta

from django.utils import timezone
from django.utils.timezone import localtime

# CORRECCIÓN 1: Importamos Horario en lugar de Disponibilidad
from domain.models import Cita, Paciente, Servicio, Horario


# ============================================================
# HORARIO DEL DENTISTA (Antes Disponibilidad, ahora Horario)
# ============================================================

def obtener_turnos_dentista_en_fecha(dentista, fecha):
    """
    Devuelve los turnos (Horario) del dentista para un día concreto.
    - fecha: date
    """
    # CORRECCIÓN: Usamos el modelo Horario
    return Horario.objects.filter(
        dentista=dentista,
        dia_semana=fecha.weekday()
    ).order_by("hora_inicio")


def es_horario_laboral_dentista(dentista, fecha, hora):
    """
    True si 'hora' cae dentro de alguno de los bloques de Horario
    del dentista para ese día.
    """
    turnos = obtener_turnos_dentista_en_fecha(dentista, fecha)
    if not turnos.exists():
        return False

    for t in turnos:
        if t.hora_inicio <= hora < t.hora_fin:
            return True
    return False


def obtener_slots_disponibles(dentista, fecha, servicio, minutos_bloque=15):
    """
    Devuelve una lista de strings 'HH:MM' con TODOS los horarios libres
    para ese día.
    """
    tz = timezone.get_current_timezone()
    # Seguridad: si el servicio no tiene duración, usamos 45 min por defecto
    dur_minutos = int(getattr(servicio, "duracion_estimada", 45) or 45)

    turnos = obtener_turnos_dentista_en_fecha(dentista, fecha)
    if not turnos.exists():
        return []

    # Citas ya reservadas de ese día
    estados_bloqueo = [
        "PENDIENTE",   # Usamos strings directos para evitar error si EstadoCita cambió
        "CONFIRMADA",
    ]
    
    # CORRECCIÓN 2: Filtramos por 'fecha' directamente (campo real en BD)
    citas = (
        Cita.objects
        .filter(
            dentista=dentista,
            fecha=fecha,  # <--- Cambio clave
            estado__in=estados_bloqueo,
        )
        .order_by("hora_inicio") # <--- Ordenamos por hora
    )

    # Preparamos lista de tuplas (datetime_inicio, datetime_fin) con zona horaria
    ocupados = []
    for c in citas:
        # Reconstruimos los datetimes porque en BD están separados
        dt_inicio = timezone.make_aware(datetime.combine(c.fecha, c.hora_inicio), tz)
        dt_fin = timezone.make_aware(datetime.combine(c.fecha, c.hora_fin), tz)
        ocupados.append((dt_inicio, dt_fin))

    step = timedelta(minutes=minutos_bloque)
    libres = []

    for turno in turnos:
        actual = timezone.make_aware(
            datetime.combine(fecha, turno.hora_inicio),
            tz
        )
        jornada_fin = timezone.make_aware(
            datetime.combine(fecha, turno.hora_fin),
            tz
        )

        while actual + timedelta(minutes=dur_minutos) <= jornada_fin:
            # Alinear a bloques de minutos_bloque (00, 15, 30, 45)
            if actual.minute % minutos_bloque != 0:
                next_min = (actual.minute // minutos_bloque + 1) * minutos_bloque
                if next_min >= 60:
                    actual = actual.replace(
                        hour=actual.hour + 1,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )
                else:
                    actual = actual.replace(
                        minute=next_min,
                        second=0,
                        microsecond=0,
                    )
                continue

            fin = actual + timedelta(minutes=dur_minutos)
            
            # Verificamos si choca con alguna cita ocupada
            choque = any(
                not (fin <= ini or actual >= fi)
                for ini, fi in ocupados
            )

            if not choque:
                libres.append(actual.strftime("%H:%M"))

            actual += step

    return libres


def sugerir_horario_cita(dentista, fecha, servicio, hora_deseada):
    """
    Usa obtener_slots_disponibles y devuelve el PRIMER datetime disponible
    >= hora_deseada. Si no hay, devuelve None.
    """
    tz = timezone.get_current_timezone()
    slots = obtener_slots_disponibles(dentista, fecha, servicio, minutos_bloque=15)

    if not slots:
        return None

    deseada_min = hora_deseada.hour * 60 + hora_deseada.minute

    mejor_slot = None
    mejor_min = None

    for s in slots:
        try:
            hh, mm = map(int, s.split(":"))
        except ValueError:
            continue
        total_min = hh * 60 + mm

        if total_min >= deseada_min:
            if mejor_min is None or total_min < mejor_min:
                mejor_min = total_min
                mejor_slot = time(hh, mm)

    if mejor_slot is None:
        # Si no hay nada >= hora_deseada, sugerimos el primer slot del día
        primero = slots[0]
        hh, mm = map(int, primero.split(":"))
        mejor_slot = time(hh, mm)

    inicio = timezone.make_aware(
        datetime.combine(fecha, mejor_slot),
        tz
    )
    return inicio


# ============================================================
# RIESGO / PENALIZACIONES
# ============================================================

def calcular_score_riesgo(paciente, dentista=None):
    """
    Calcula un score de riesgo simple basado en inasistencias y cancelaciones.
    0 = sin riesgo, 100 = riesgo máximo.
    """
    qs = Cita.objects.filter(paciente=paciente)
    if dentista is not None:
        qs = qs.filter(dentista=dentista)

    total = qs.count()
    if total == 0:
        return 0

    inasistencias = qs.filter(estado="INASISTENCIA").count()
    canceladas = qs.filter(estado="CANCELADA").count()

    peso_inasistencia = 3
    peso_cancelada = 1

    score_bruto = inasistencias * peso_inasistencia + canceladas * peso_cancelada
    score = min(100, score_bruto * 10)  # normalización simple
    return score


def calcular_penalizacion_paciente(paciente, dentista=None):
    """
    Devuelve un dict con el estado de penalización del paciente.
    """
    # Seguridad extra
    if not paciente or not getattr(paciente, "pk", None):
        return {
            "estado": "sin_penalizacion",
            "recargo": 0,
            "dias_transcurridos": None,
            "inasistencias": 0,
        }

    hoy = timezone.localdate()

    qs = Cita.objects.filter(
        paciente=paciente,
        estado="INASISTENCIA",
    )
    if dentista is not None:
        qs = qs.filter(dentista=dentista)

    # CORRECCIÓN 3: Ordenar por fecha y hora (campos reales)
    qs = qs.order_by("-fecha", "-hora_inicio")
    inasistencias_count = qs.count()

    if inasistencias_count < 3:
        return {
            "estado": "sin_penalizacion",
            "recargo": 0,
            "dias_transcurridos": None,
            "inasistencias": inasistencias_count,
        }

    ultima = qs.first()
    # Reconstruimos fecha/hora
    fecha_ultima = ultima.fecha
    dias_transcurridos = (hoy - fecha_ultima).days

    if dias_transcurridos > 5:
        estado = "disabled"
    else:
        estado = "pending"

    return {
        "estado": estado,
        "recargo": 300,
        "dias_transcurridos": dias_transcurridos,
        "inasistencias": inasistencias_count,
    }


def procesar_inasistencia(cita):
    """
    Marca una cita como INASISTENCIA y devuelve un mensaje legible para el dentista.
    """
    if cita.estado == "INASISTENCIA":
        return "La cita ya estaba marcada como inasistencia."

    cita.estado = "INASISTENCIA"
    cita.save()

    info = calcular_penalizacion_paciente(
        paciente=cita.paciente,
        dentista=cita.dentista,
    )

    inasistencias = info["inasistencias"]
    estado = info["estado"]

    if inasistencias < 3:
        return (
            f"Inasistencia registrada. El paciente acumula {inasistencias} "
            "inasistencias con este consultorio."
        )

    if estado == "pending":
        return (
            "Inasistencia registrada. El paciente ha alcanzado 3 inasistencias y "
            "queda penalizado con una cuota de $300. Tiene 5 días para regularizarse."
        )

    if estado == "disabled":
        return (
            "Inasistencia registrada. El paciente ha superado el plazo de 5 días "
            "sin cubrir la penalización, por lo que su cuenta se considera SUSPENDIDA."
        )

    return (
        "Inasistencia registrada. Revisa la sección de penalizaciones para más detalles."
    )