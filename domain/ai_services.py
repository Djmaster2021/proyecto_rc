# domain/ai_services.py

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.utils import timezone
from django.utils.timezone import localtime
from django.conf import settings
from domain.notifications import enviar_correo_penalizacion

# CORRECCIÓN 1: Importamos Horario en lugar de Disponibilidad
from domain.models import Cita, Paciente, Servicio, Horario, PenalizacionLog, Pago


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
    Calcula un score de riesgo de 0 a 100 combinando:
    - Inasistencias (peso alto)
    - Cancelaciones (peso medio)
    - Pagos pendientes (peso medio)
    - Frecuencia de reprogramaciones (peso bajo)
    """
    qs = Cita.objects.filter(paciente=paciente)
    if dentista is not None:
        qs = qs.filter(dentista=dentista)

    total = qs.count()
    if total == 0:
        return 0

    inasistencias = qs.filter(estado="INASISTENCIA").count()
    canceladas = qs.filter(estado="CANCELADA").count()
    reprogramadas = qs.filter(veces_reprogramada__gte=1).count()
    pagos_pend = Pago.objects.filter(cita__paciente=paciente, estado="PENDIENTE").count()

    # Pesos ajustados
    peso_inasistencia = 5
    peso_cancelada = 2
    peso_reprog = 1
    peso_pago = 3

    score_bruto = (
        inasistencias * peso_inasistencia
        + canceladas * peso_cancelada
        + reprogramadas * peso_reprog
        + pagos_pend * peso_pago
    )
    # Normalizamos: cada punto suma ~8 hasta un máximo de 100
    score = min(100, score_bruto * 8)
    return score


def calcular_penalizacion_paciente(paciente, dentista=None):
    """
    Devuelve un dict con el estado de penalización del paciente.

    Regla:
    - 1ra inasistencia confirmada: advertencia (warning)
    - 2da inasistencia confirmada: suspensión automática + cuota $300
      (se mantiene en pending hasta 5 días, luego pasa a disabled)
    """
    if not paciente or not getattr(paciente, "pk", None):
        return {
            "estado": "sin_penalizacion",
            "recargo": 0,
            "dias_restantes": None,
            "inasistencias": 0,
            "fecha_limite": None,
        }

    hoy = timezone.localdate()

    qs = Cita.objects.filter(
        paciente=paciente,
        estado="INASISTENCIA",
    )
    if dentista is not None:
        qs = qs.filter(dentista=dentista)

    qs = qs.order_by("-fecha", "-hora_inicio")
    inasistencias_count = qs.count()

    # Datos base
    estado = "sin_penalizacion"
    recargo = 0
    dias_restantes = None
    fecha_limite = None

    # Revisamos si hay un cargo pendiente de penalización
    penalizacion = (
        Pago.objects.filter(
            cita__paciente=paciente,
            cita__estado="INASISTENCIA",
            estado="PENDIENTE",
            monto__gte=Decimal("300"),
        )
        .order_by("-created_at")
        .first()
    )

    if penalizacion:
        recargo = float(penalizacion.monto)
        fecha_penal = penalizacion.created_at.date()
        dias_restantes = max(0, 5 - (hoy - fecha_penal).days)
        fecha_limite = fecha_penal + timezone.timedelta(days=5)
        estado = "pending" if dias_restantes > 0 else "disabled"
    elif inasistencias_count == 1:
        # Primer falta: solo advertencia
        estado = "warning"
        recargo = 0
        dias_restantes = None
    elif inasistencias_count >= 2:
        # Segunda falta sin pago registrado (fallback)
        estado = "pending"
        recargo = 300
        dias_restantes = 5

    return {
        "estado": estado,
        "recargo": recargo,
        "dias_restantes": dias_restantes,
        "inasistencias": inasistencias_count,
        "fecha_limite": fecha_limite,
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

    mensaje = "Inasistencia registrada."

    if inasistencias == 1:
        # Solo advertencia en la primera falta
        PenalizacionLog.objects.create(
            dentista=cita.dentista,
            paciente=cita.paciente,
            accion="ADVERTENCIA",
            motivo="Primera inasistencia confirmada.",
            monto=Decimal("0"),
        )
        mensaje = (
            "Inasistencia registrada. Advertencia emitida: la siguiente falta generará un cargo de $300."
        )
        _enviar_correo_penalizacion(cita, advertencia=True)
    else:
        # Desde la segunda falta generamos el pago pendiente
        pago_penal, creado = Pago.objects.get_or_create(
            cita=cita,
            defaults={
                "monto": Decimal("300.00"),
                "metodo": "EFECTIVO",
                "estado": "PENDIENTE",
            },
        )
        if not creado and pago_penal.estado != "COMPLETADO":
            pago_penal.monto = Decimal("300.00")
            pago_penal.estado = "PENDIENTE"
            pago_penal.save(update_fields=["monto", "estado"])

        PenalizacionLog.objects.create(
            dentista=cita.dentista,
            paciente=cita.paciente,
            accion="AUTO_PENALIZAR",
            motivo="Inasistencia reiterada. Cargo automático.",
            monto=Decimal("300.00"),
        )

        if inasistencias >= 2:
            user = getattr(cita.paciente, "user", None)
            if user and user.is_active:
                user.is_active = False
                user.save(update_fields=["is_active"])
            mensaje = (
                "Inasistencia registrada. Penalización de $300 generada y la cuenta se suspendió "
                "automáticamente hasta liquidar."
            )
        _enviar_correo_penalizacion(cita, advertencia=False)

    return mensaje


def _enviar_correo_penalizacion(cita, advertencia=True):
    """
    Email sencillo al paciente notificando advertencia o penalización.
    """
    correo = getattr(getattr(cita.paciente, "user", None), "email", None)
    if not correo:
        return

    if advertencia:
        motivo = "Advertencia por inasistencia. Si vuelves a faltar se generará una penalización."
        recargo = 0
    else:
        motivo = "Penalización por inasistencia reiterada. Tu cuenta se suspende hasta cubrir el pago."
        recargo = 300

    enviar_correo_penalizacion(
        email_destino=correo,
        nombre_paciente=cita.paciente.nombre,
        motivo=motivo,
        recargo=recargo,
        dias_limite=5,
    )
