# ============================================================
#  VIEWS DEL DENTISTA — SISTEMA RC DENTAL PRO (FINAL)
# ============================================================

import json
import csv
from datetime import date, datetime, timedelta
import re
from decimal import Decimal
import os
from io import StringIO, BytesIO
from pathlib import Path
from django.conf import settings 
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.db.models import Sum, Q, Count
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

# IMPORTAMOS TODOS LOS MODELOS
from domain.models import (
    PenalizacionLog,
    AvisoDentista,
    Cita,
    Dentista,
    Horario,
    ComprobantePago,
    Paciente,
    Pago,
    Servicio,
    Diente,
    TicketSoporte,
)
from domain.ai_services import calcular_penalizacion_paciente, procesar_inasistencia
from domain.notifications import (
    enviar_correo_confirmacion_cita,
    enviar_correo_penalizacion,
    enviar_correo_ticket_soporte,
    registrar_aviso_dentista,
)

def _guardar_aviso(dentista, mensaje):
    """Wrapper seguro para registrar avisos sin romper el flujo principal."""
    try:
        registrar_aviso_dentista(dentista, mensaje)
    except Exception as exc:
        print(f"[WARN] Aviso no guardado: {exc}")


def _reactivar_paciente_por_pago(pago_obj):
    """
    Reactiva cuenta cuando se registra pago ligado a una cita INASISTENCIA (penalización).
    """
    cita = getattr(pago_obj, "cita", None)
    paciente = getattr(cita, "paciente", None)
    user = getattr(paciente, "user", None)

    if not cita or not paciente or cita.estado != "INASISTENCIA":
        return

    if user and not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])

    try:
        ultimo = (
            PenalizacionLog.objects.filter(paciente=paciente, accion="REACTIVAR")
            .order_by("-created_at")
            .first()
        )
        if not ultimo or ultimo.created_at.date() < timezone.localdate():
            PenalizacionLog.objects.create(
                dentista=cita.dentista,
                paciente=paciente,
                accion="REACTIVAR",
                motivo="Reactivación automática tras pago de penalización.",
                monto=pago_obj.monto,
            )
    except Exception as exc:
        print(f"[WARN] No se pudo registrar reactivación automática: {exc}")

def _build_weeks(dentista, start_date, end_date, hoy, hora_actual):
    """
    Construye una lista de semanas (listas de días) desde start_date hasta end_date (inclusive),
    con datos de citas y estado laboral. Siempre excluye días pasados (el caller ya ajusta start_date).
    """
    dias = []
    total_dias = (end_date - start_date).days + 1

    for offset in range(total_dias):
        fecha = start_date + timedelta(days=offset)
        citas_dia = Cita.objects.filter(dentista=dentista, fecha=fecha).exclude(estado="CANCELADA").order_by("hora_inicio")

        citas_info = []
        for c in citas_dia:
            pasada = (fecha < hoy) or (fecha == hoy and c.hora_fin < hora_actual)
            citas_info.append({
                "obj": c,
                "es_mia": c.dentista == dentista,
                "clase_extra": "ghost-mode" if pasada else "",
            })

        dias.append({
            "fecha": fecha,
            "tipo_dia": "laboral" if Horario.objects.filter(dentista=dentista, dia_semana=fecha.isoweekday()).exists() else "descanso",
            "citas": citas_info,
        })

    # Agrupar en semanas de 7 días (empezando hoy, no necesariamente lunes)
    semanas = [dias[i:i+7] for i in range(0, len(dias), 7)]
    return semanas

def _build_resumenes(dentista, hoy, hora_actual):
    citas_hoy = (
        Cita.objects.filter(dentista=dentista, fecha=hoy)
        .exclude(estado="CANCELADA")
        .order_by("hora_inicio")
    )
    en_curso = citas_hoy.filter(hora_inicio__lte=hora_actual, hora_fin__gt=hora_actual).first()
    siguiente = citas_hoy.filter(hora_inicio__gt=hora_actual).first()
    resumen_agenda = {
        "paciente": en_curso.paciente.nombre if en_curso else (siguiente.paciente.nombre if siguiente else None),
        "servicio": en_curso.servicio.nombre if en_curso else (siguiente.servicio.nombre if siguiente else None),
        "fecha": hoy,
        "horario": f"{en_curso.hora_inicio.strftime('%H:%M')} - {en_curso.hora_fin.strftime('%H:%M')}" if en_curso else (f"{siguiente.hora_inicio.strftime('%H:%M')} - {siguiente.hora_fin.strftime('%H:%M')}" if siguiente else None),
        "estado": "en_curso" if en_curso else ("pendiente" if siguiente else "libre"),
        "label": "En curso" if en_curso else ("Siguiente" if siguiente else "Libre"),
    }

    estado_counts = {
        "confirmada": Cita.objects.filter(dentista=dentista, estado="CONFIRMADA").count(),
        "pendiente": Cita.objects.filter(dentista=dentista, estado="PENDIENTE").count(),
        "completada": Cita.objects.filter(dentista=dentista, estado="COMPLETADA").count(),
        "cancelada": Cita.objects.filter(dentista=dentista, estado="CANCELADA").count(),
    }
    resumen_hoy = {
        "total": citas_hoy.count(),
        "finalizadas": citas_hoy.filter(estado="COMPLETADA").count(),
    }
    return resumen_agenda, estado_counts, resumen_hoy

# ============================================================
#  1. SISTEMA DE CORREOS INTELIGENTE
# ============================================================

def _validar_telefono_10d(telefono):
    """Normaliza a dígitos y valida exactamente 10."""
    telefono = re.sub(r"\D", "", (telefono or ""))
    return telefono if len(telefono) == 10 else None


def _get_paciente_email(paciente):
    """Recupera el email desde el usuario vinculado al paciente."""
    user = getattr(paciente, "user", None)
    return getattr(user, "email", None)

def procesar_notificacion_cita(cita, origen="DENTISTA", accion="CREADA"):
    """
    Envía correos automáticos dependiendo de quién crea/modifica la cita.
    """
    try:
        # Contexto base para las plantillas
        contexto_base = {
            'paciente_nombre': cita.paciente.nombre,
            'servicio': cita.servicio.nombre,
            'fecha': cita.fecha.strftime('%d de %B de %Y'),
            'hora': cita.hora_inicio.strftime('%H:%M'),
            'dentista': cita.dentista.nombre,
            'telefono': cita.paciente.telefono
        }

        # --- CASO 1: DENTISTA AGENDA (Manual) ---
        if origen == "DENTISTA" and accion == "CREADA":
            email_paciente = _get_paciente_email(cita.paciente)
            if email_paciente:
                contexto = contexto_base.copy()
                contexto['titulo'] = "Cita Agendada"
                contexto['mensaje'] = "El consultorio ha agendado una nueva cita para ti."
                _enviar_html(
                    asunto=f"📅 Cita Agendada: {cita.fecha.strftime('%d/%m')}",
                    template='dentista/email_paciente.html',
                    contexto=contexto,
                    destinatario=email_paciente
                )

        # --- CASO 2: PACIENTE AGENDA (Web) ---
        elif origen == "PACIENTE" and accion == "CREADA":
            # Confirmación al paciente
            email_paciente = _get_paciente_email(cita.paciente)
            if email_paciente:
                contexto_p = contexto_base.copy()
                contexto_p['titulo'] = "Solicitud Recibida"
                contexto_p['mensaje'] = "Hemos recibido tu solicitud de cita. Te esperamos."
                _enviar_html(
                    asunto="✅ Tu cita ha sido reservada",
                    template='dentista/email_paciente.html',
                    contexto=contexto_p,
                    destinatario=email_paciente
                )
            
            # Alerta al dentista
            email_dentista = getattr(cita.dentista.user, "email", None)
            if email_dentista:
                _enviar_html(
                    asunto=f"🔔 Nueva Cita Web: {cita.paciente.nombre}",
                    template='dentista/email_dentista.html',
                    contexto=contexto_base,
                    destinatario=email_dentista
                )

        # --- CASO 3: CONFIRMACIÓN DE CITA ---
        elif accion == "CONFIRMADA":
            email_paciente = _get_paciente_email(cita.paciente)
            if email_paciente:
                contexto = contexto_base.copy()
                contexto['titulo'] = "Cita Confirmada"
                contexto['mensaje'] = "Tu cita está 100% confirmada. Recuerda llegar 5 min antes."
                _enviar_html(
                    asunto="✅ Confirmación de Cita RC Dental",
                    template='dentista/email_paciente.html',
                    contexto=contexto,
                    destinatario=email_paciente
                )

    except Exception as e:
        print(f"Error enviando correos: {e}")

def _enviar_html(asunto, template, contexto, destinatario):
    """Renderiza y envía el correo usando SMTP."""
    try:
        html_content = render_to_string(template, contexto)
        text_content = strip_tags(html_content)
        
        send_mail(
            subject=asunto,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            html_message=html_content,
            fail_silently=True
        )
        print(f"--> Correo enviado a {destinatario}")
    except Exception as e:
        print(f"Error SMTP: {e}")


# ============================================================
#  2. FUNCIONES DE IA / CÁLCULOS
# ============================================================

def calcular_riesgo_paciente(paciente):
    """
    Reusa la lógica central de riesgo (domain.ai_services) para mostrar
    porcentaje y nivel en el dashboard del dentista.
    """
    from domain.ai_services import calcular_score_riesgo

    riesgo_percent = calcular_score_riesgo(paciente)

    if riesgo_percent >= 70:
        lvl, col = "Alto", "badge-red"
    elif riesgo_percent >= 35:
        lvl, col = "Medio", "badge-yellow"
    else:
        lvl, col = "Bajo", "badge-green"

    return {"paciente": paciente.nombre, "porcentaje": riesgo_percent, "nivel": lvl, "color": col}

def optimizar_agenda(citas_dia):
    sugerencias = []
    citas = sorted(citas_dia, key=lambda x: x.hora_inicio)
    for i in range(len(citas) - 1):
        fin = datetime.combine(citas[i].fecha, citas[i].hora_fin)
        ini = datetime.combine(citas[i+1].fecha, citas[i+1].hora_inicio)
        # Si hay hueco mayor a 20 min
        if (ini - fin).seconds // 60 >= 20:
            sugerencias.append(f"Hueco libre entre {citas[i].paciente.nombre} y {citas[i+1].paciente.nombre}.")
    return sugerencias


# ============================================================
#  3. DASHBOARD Y AGENDA
# ============================================================

@login_required
def dashboard_dentista(request):
    dentista = Dentista.objects.filter(user=request.user).first()
    if not dentista:
        # Si el usuario no es dentista, redirige a su panel de paciente
        return redirect("paciente:dashboard")
    hoy = date.today()
    hora_actual = timezone.localtime().time()

    citas_hoy = (
        Cita.objects.filter(dentista=dentista, fecha=hoy)
        .exclude(estado__in=["CANCELADA", "INASISTENCIA"])
        .select_related("paciente", "servicio")
        .order_by("hora_inicio")
    )
    inicio_mes = hoy.replace(day=1)
    
    # KPIs
    kpi_pacs = Paciente.objects.filter(dentista=dentista).count()
    kpi_pend = Cita.objects.filter(dentista=dentista, estado="PENDIENTE").count()
    ingresos = Pago.objects.filter(cita__dentista=dentista, estado="COMPLETADO", created_at__date__gte=inicio_mes).aggregate(Sum("monto"))["monto__sum"] or 0

    # Próxima Cita
    prox = Cita.objects.filter(dentista=dentista, estado__in=["PENDIENTE", "CONFIRMADA"]).filter(Q(fecha__gt=hoy)|Q(fecha=hoy, hora_fin__gt=hora_actual)).order_by("fecha", "hora_inicio").first()

    # Radar (Mini calendario de 30 días)
    if inicio_mes.month == 12: sig = inicio_mes.replace(year=inicio_mes.year+1, month=1, day=1)
    else: sig = inicio_mes.replace(month=inicio_mes.month+1, day=1)
    
    calendario = []
    # Rango de 60 días a partir de hoy (incluye hoy)
    start_date = hoy
    end_date = hoy + timedelta(days=60)
    total_dias = (end_date - start_date).days + 1
    dias_es = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]

    for i in range(total_dias):
        f = start_date + timedelta(days=i)
        cs = (
            Cita.objects.filter(dentista=dentista, fecha=f)
            .exclude(estado="CANCELADA")
            .select_related("paciente", "servicio")
            .order_by("hora_inicio")
        )
        procesadas = []
        for c in cs:
            pasada = (f < hoy) or (f == hoy and c.hora_fin < hora_actual)
            procesadas.append({
                "paciente": c.paciente.nombre,
                "hora": c.hora_inicio.strftime("%H:%M"),
                "servicio": c.servicio.nombre if c.servicio else "",
                "clase_estado": "cita-pasada" if pasada else c.estado.lower()
            })
        calendario.append({
            "dia": f,
            "label_dia": dias_es[f.weekday()],
            "clases": "hoy" if f == hoy else "",
            "citas": procesadas,
        })

    avisos = AvisoDentista.objects.filter(dentista=dentista).order_by("-created_at")[:15]

    return render(request, "dentista/dashboard.html", {
        "dentista": dentista, "citas_hoy": citas_hoy, "kpi_pacientes": kpi_pacs, "kpi_pendientes": kpi_pend,
        "ingresos_mes": ingresos, "proxima_cita": prox, "calendario_dias": calendario,
        "riesgos": [calcular_riesgo_paciente(p) for p in Paciente.objects.filter(dentista=dentista)],
        "sugerencias": optimizar_agenda(citas_hoy),
        "pagos": Pago.objects.filter(cita__dentista=dentista).order_by("-created_at")[:5],
        "notificaciones": avisos,
    })

@login_required
def agenda_dentista(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    hoy = date.today()
    hora_actual = timezone.localtime().time()
    fin_rango = hoy + timedelta(days=60)
    semanas = _build_weeks(dentista, hoy, fin_rango, hoy, hora_actual)
    resumen_agenda, estado_counts, resumen_hoy = _build_resumenes(dentista, hoy, hora_actual)

    return render(request, "dentista/agenda.html", {
        "dentista": dentista,
        "semanas": semanas,
        "fecha_actual": hoy,
        "modo": "todo",
        "resumen_agenda": resumen_agenda,
        "estado_counts": estado_counts,
        "resumen_hoy": resumen_hoy,
    })


@login_required
def agenda_modo(request, modo):
    """
    Vista ligera para alternar modos de la agenda (día, semana, mes).
    Se reutilizan datos simples para que los enlaces en las plantillas no rompan.
    """
    dentista = get_object_or_404(Dentista, user=request.user)
    hoy = date.today()
    hora_actual = timezone.localtime().time()
    fin_rango = hoy + timedelta(days=60)

    if modo == "dia":
        fecha_str = request.GET.get("fecha")
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else hoy
        except (TypeError, ValueError):
            fecha = hoy
        # Asegurar rango válido
        if fecha < hoy:
            fecha = hoy
        if fecha > fin_rango:
            fecha = fin_rango
        semanas = _build_weeks(dentista, fecha, fecha, hoy, hora_actual)
        resumen_agenda, estado_counts, resumen_hoy = _build_resumenes(dentista, hoy, hora_actual)
        return render(request, "dentista/agenda.html", {
            "dentista": dentista,
            "semanas": semanas,
            "fecha_actual": hoy,
            "modo": "dia",
            "resumen_agenda": resumen_agenda,
            "estado_counts": estado_counts,
            "resumen_hoy": resumen_hoy,
        })

    if modo == "semana":
        fin_semana = min(fin_rango, hoy + timedelta(days=6))
        semanas = _build_weeks(dentista, hoy, fin_semana, hoy, hora_actual)
        resumen_agenda, estado_counts, resumen_hoy = _build_resumenes(dentista, hoy, hora_actual)
        return render(request, "dentista/agenda.html", {
            "dentista": dentista,
            "semanas": semanas,
            "fecha_actual": hoy,
            "modo": "semana",
            "resumen_agenda": resumen_agenda,
            "estado_counts": estado_counts,
            "resumen_hoy": resumen_hoy,
        })

    # Modo mes (o default): mostrar rango completo hasta 60 días
    semanas = _build_weeks(dentista, hoy, fin_rango, hoy, hora_actual)
    resumen_agenda, estado_counts, resumen_hoy = _build_resumenes(dentista, hoy, hora_actual)
    return render(request, "dentista/agenda.html", {
        "dentista": dentista,
        "semanas": semanas,
        "fecha_actual": hoy,
        "modo": "mes",
        "resumen_agenda": resumen_agenda,
        "estado_counts": estado_counts,
        "resumen_hoy": resumen_hoy,
    })


# ============================================================
#  4. CITAS (CRUD Y LÓGICA)
# ============================================================

@login_required
def crear_cita_manual(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    
    if request.method == "POST":
        p_id = request.POST.get("paciente")
        s_id = request.POST.get("servicio")
        f_str = request.POST.get("fecha")
        h_str = request.POST.get("hora")
        metodo_pago = request.POST.get("metodo_pago", "EFECTIVO").upper()
        monto_raw = request.POST.get("monto", "").strip()
        
        if p_id and s_id and f_str and h_str:
            try:
                f = datetime.strptime(f_str, "%Y-%m-%d").date()
                h = datetime.strptime(h_str, "%H:%M").time()
                hoy = date.today()
                if f < hoy:
                    messages.error(request, "No puedes agendar en fecha pasada.")
                    return redirect("dentista:crear_cita_manual")

                s = Servicio.objects.get(id=s_id)
                if s.dentista_id != dentista.id:
                    messages.error(request, "Debes elegir un servicio del propio consultorio.")
                    return redirect("dentista:crear_cita_manual")
                paciente_obj = get_object_or_404(Paciente, id=p_id, dentista=dentista)

                # Validar monto manual (opcional)
                try:
                    monto_decimal = Decimal(monto_raw) if monto_raw else s.precio
                except Exception:
                    messages.error(request, "Monto inválido.")
                    return redirect("dentista:crear_cita_manual")

                if metodo_pago not in ["EFECTIVO", "TRANSFERENCIA", "TARJETA", "MERCADOPAGO"]:
                    metodo_pago = "EFECTIVO"
                
                # Crear la cita
                nueva_cita = Cita.objects.create(
                    dentista=dentista,
                    paciente=paciente_obj,
                    servicio=s,
                    fecha=f,
                    hora_inicio=h,
                    hora_fin=(datetime.combine(f, h) + timedelta(minutes=s.duracion_estimada)).time(),
                    estado="PENDIENTE"
                )
                # Crear pago pendiente para reflejarlo en paneles
                try:
                    Pago.objects.get_or_create(
                        cita=nueva_cita,
                        defaults={
                            "monto": monto_decimal,
                            "metodo": metodo_pago,
                            "estado": "PENDIENTE",
                        },
                    )
                except Exception as exc:
                    print(f"[WARN] No se pudo crear pago pendiente: {exc}")

                _guardar_aviso(
                    dentista,
                    f"Cita creada manualmente para {paciente_obj.nombre} el {f.strftime('%d/%m')} {h.strftime('%H:%M')} ({s.nombre})",
                )
                
                # NOTIFICACIÓN AUTOMÁTICA
                procesar_notificacion_cita(nueva_cita, origen="DENTISTA", accion="CREADA")
                try:
                    email_dest = getattr(getattr(paciente_obj, "user", None), "email", None)
                    if email_dest:
                        enviar_correo_confirmacion_cita(nueva_cita)
                    else:
                        messages.warning(request, "Cita creada, pero el paciente no tiene correo registrado.")
                except Exception as exc:
                    print(f"[WARN] No se pudo enviar correo de confirmación: {exc}")
                
                messages.success(request, "Cita creada y notificada al paciente.")
                return redirect("dentista:agenda")
                
            except Exception as e:
                messages.error(request, f"Error al crear la cita: {e}")

    return render(request, "dentista/crear_cita_manual.html", {
        "dentista": dentista,
        "pacientes": Paciente.objects.filter(dentista=dentista),
        "servicios": Servicio.objects.filter(dentista=dentista, activo=True),
        "fecha_min": date.today().strftime("%Y-%m-%d"),
        "fecha_max": (date.today()+timedelta(days=60)).strftime("%Y-%m-%d")
    })

@login_required
@require_POST
def eliminar_cita(request, id):
    cita = get_object_or_404(Cita, id=id, dentista__user=request.user)
    # Opcional: Notificar cancelación antes de borrar
    cita.delete()
    messages.success(request, "Cita eliminada.")
    return redirect("dentista:agenda")

@login_required
def consulta(request, id):
    cita = get_object_or_404(Cita, id=id, dentista__user=request.user)
    
    if request.method == "POST":
        cita.notas = request.POST.get("notas_clinicas", "")
        if request.FILES.get("archivo_adjunto"): 
            cita.archivo_adjunto = request.FILES.get("archivo_adjunto")
        
        aviso_text = None
        if "pagado" in request.POST:
            # Flujo de pago rápido desde consulta
            cita.estado = "COMPLETADA"
            monto_registrado = request.POST.get("monto", cita.servicio.precio)
            pago_obj, _ = Pago.objects.update_or_create(
                cita=cita, 
                defaults={"monto": monto_registrado, "estado": "COMPLETADO", "metodo": "EFECTIVO"}
            )
            aviso_text = f"Pago registrado en consulta para {cita.paciente.nombre}: ${pago_obj.monto} ({pago_obj.metodo})"
        else:
            # Confirmación manual
            if cita.estado not in ["COMPLETADA", "CANCELADA"]:
                if cita.estado != "CONFIRMADA":
                    cita.estado = "CONFIRMADA"
                    # NOTIFICACIÓN DE CONFIRMACIÓN
                    procesar_notificacion_cita(cita, origen="DENTISTA", accion="CONFIRMADA")
                    aviso_text = (
                        f"Cita confirmada para {cita.paciente.nombre} el "
                        f"{cita.fecha.strftime('%d/%m')} {cita.hora_inicio.strftime('%H:%M')}"
                    )
        
        cita.save()
        if aviso_text:
            _guardar_aviso(cita.dentista, aviso_text)
        messages.success(request, "Consulta actualizada.")
        return redirect("dentista:consulta", id=cita.id)
        
    return render(request, "dentista/consulta.html", {
        "dentista": cita.dentista, 
        "cita": cita, 
        "pago": getattr(cita, 'pago_relacionado', None)
    })

@login_required
def obtener_slots_disponibles(request):
    """API para obtener horas libres en crear_cita_manual"""
    dentista = get_object_or_404(Dentista, user=request.user)
    fecha_str, s_id = request.GET.get('fecha'), request.GET.get('servicio_id')
    
    if not fecha_str or not s_id:
        return JsonResponse({'slots': []})

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        servicio = Servicio.objects.get(id=s_id, dentista=dentista)
        duracion = servicio.duracion_estimada
    except Servicio.DoesNotExist:
        return JsonResponse({'slots': []})
    except Exception:
        return JsonResponse({'slots': []})

    horarios = Horario.objects.filter(dentista=dentista, dia_semana=fecha.isoweekday())
    if not horarios: return JsonResponse({'slots': [], 'mensaje': 'Día no laboral'})

    ocupados = [(datetime.combine(fecha, c.hora_inicio), datetime.combine(fecha, c.hora_fin)) 
                for c in Cita.objects.filter(dentista=dentista, fecha=fecha).exclude(estado__in=['CANCELADA', 'INASISTENCIA'])]
    
    slots = []
    for h in horarios:
        cursor = datetime.combine(fecha, h.hora_inicio)
        fin = datetime.combine(fecha, h.hora_fin)
        while cursor + timedelta(minutes=duracion) <= fin:
            fin_slot = cursor + timedelta(minutes=duracion)
            if not any(cursor < o_fin and fin_slot > o_ini for o_ini, o_fin in ocupados):
                if fecha > date.today() or (fecha == date.today() and cursor > datetime.now()):
                    slots.append({'hora': cursor.strftime("%H:%M"), 'recomendado': False})
            cursor += timedelta(minutes=15)
    
    if slots: slots[0]['recomendado'] = True
    return JsonResponse({'slots': slots})


# ============================================================
#  5. SERVICIOS (CATÁLOGO CRUD)
# ============================================================

@login_required
def servicios(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    q = request.GET.get("q", "").strip()
    qs = Servicio.objects.filter(dentista=dentista).order_by("nombre")
    
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    
    # Fallback de descripciones breves para mostrar algo útil aunque el campo esté vacío
    standard_desc = {
        "limpieza": "Profilaxis corta con ultrasonido y pulido.",
        "consulta": "Evaluación inicial y plan de tratamiento.",
        "control": "Revisión de seguimiento y ajustes.",
        "extracción": "Extracción simple con anestesia local.",
        "blanqueamiento": "Aclarado dental con gel profesional.",
        "resina": "Restauración con resina compuesta.",
        "endodoncia": "Tratamiento de conducto para salvar la pieza.",
        "ortodoncia": "Alineación con brackets o alineadores.",
        "alineador": "Férula transparente removible para mover dientes.",
    }
    for s in qs:
        key = (s.nombre or "").strip().lower()
        desc = (s.descripcion or "").strip()
        texto_base = standard_desc.get(key)
        if texto_base:
            s.descripcion_mostrar = texto_base
        elif desc:
            s.descripcion_mostrar = desc
        else:
            s.descripcion_mostrar = f"{s.nombre} — agrega una breve descripción (objetivo, materiales, alcance)."

    return render(request, "dentista/servicios.html", {
        "dentista": dentista, "servicios": qs, "query": q, "total": qs.count()
    })

@login_required
def servicio_crear(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    if request.method == "POST":
        try:
            Servicio.objects.create(
                dentista=dentista,
                nombre=request.POST.get("nombre", "").strip(),
                descripcion=request.POST.get("descripcion", "").strip(),
                precio=Decimal(request.POST.get("precio", "0")),
                duracion_estimada=int(request.POST.get("duracion", "30")),
                activo=True
            )
            messages.success(request, "Servicio creado.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return redirect("dentista:servicios")

@login_required
def servicio_editar(request, id):
    dentista = get_object_or_404(Dentista, user=request.user)
    servicio = get_object_or_404(Servicio, id=id, dentista=dentista)

    if request.method == "POST":
        try:
            servicio.nombre = request.POST.get("nombre")
            servicio.descripcion = request.POST.get("descripcion")
            servicio.precio = Decimal(request.POST.get("precio"))
            servicio.duracion_estimada = int(request.POST.get("duracion"))
            servicio.save()
            messages.success(request, "Servicio actualizado.")
        except Exception as e:
            messages.error(request, f"Error actualizando: {e}")

    return redirect("dentista:servicios")

@login_required
def servicio_toggle_estado(request, id):
    dentista = get_object_or_404(Dentista, user=request.user)
    servicio = get_object_or_404(Servicio, id=id, dentista=dentista)
    if request.method == "POST":
        servicio.activo = not servicio.activo
        servicio.save()
        messages.success(request, "Estado actualizado.")
    return redirect("dentista:servicios")

@login_required
def servicio_eliminar(request, id):
    dentista = get_object_or_404(Dentista, user=request.user)
    servicio = get_object_or_404(Servicio, id=id, dentista=dentista)
    if request.method == "POST":
        servicio.delete()
        messages.success(request, "Servicio eliminado.")
    return redirect("dentista:servicios")


# ============================================================
#  6. PACIENTES Y ODONTOGRAMA
# ============================================================

@login_required
def pacientes(request):
    d = get_object_or_404(Dentista, user=request.user)
    qs = Paciente.objects.filter(dentista=d).order_by("nombre")
    if q := request.GET.get("q", "").strip(): 
        qs = qs.filter(Q(nombre__icontains=q) | Q(telefono__icontains=q))
    return render(request, "dentista/pacientes.html", {"dentista": d, "pacientes": qs, "query": q})

@login_required
def registrar_paciente(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    
    if request.method == "POST":
        # 1. Obtener datos del formulario
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        
        # 2. Validaciones básicas
        if not email or not password or not nombre:
            messages.error(request, "Correo, contraseña y nombre son obligatorios.")
            return render(request, "dentista/registrar_paciente.html", {"dentista": dentista})
        if not (telefono_validado := _validar_telefono_10d(telefono)):
            messages.error(request, "El teléfono debe tener exactamente 10 dígitos numéricos.")
            return render(request, "dentista/registrar_paciente.html", {"dentista": dentista})
        if Paciente.objects.filter(dentista=dentista, telefono=telefono_validado).exists():
            messages.error(request, "Ya existe un paciente con este teléfono.")
            return render(request, "dentista/registrar_paciente.html", {"dentista": dentista})
        if Paciente.objects.filter(dentista=dentista, nombre__iexact=nombre).exists():
            messages.error(request, "Ya existe un paciente con ese nombre.")
            return render(request, "dentista/registrar_paciente.html", {"dentista": dentista})
            
        # 3. Verificar si el correo ya existe
        usuarios_email = User.objects.filter(email=email)
        if usuarios_email.exists():
            messages.error(request, "Este correo ya está registrado en el sistema.")
            return render(request, "dentista/registrar_paciente.html", {"dentista": dentista})
        try:
            nuevo_usuario = User.objects.create_user(
                username=email, 
                email=email, 
                password=password,
                first_name=nombre
            )
        except Exception as e:
            messages.error(request, f"No se pudo crear el usuario: {e}")
            return render(request, "dentista/registrar_paciente.html", {"dentista": dentista})

        try:
            # 4. Crear el Paciente (Perfil Clínico)
            paciente = Paciente(
                user=nuevo_usuario,  # VINCULAMOS AL USUARIO CREADO
                dentista=dentista,
                nombre=nombre,
                telefono=telefono_validado,
                direccion=request.POST.get("direccion", ""),
                antecedentes=request.POST.get("antecedentes", "")
            )

            if f := request.POST.get("fecha_nacimiento"):
                paciente.fecha_nacimiento = datetime.strptime(f, "%Y-%m-%d").date()
            
            if request.FILES.get("imagen"):
                paciente.imagen = request.FILES.get("imagen")
                
            paciente.save()

            # OPCIONAL: Enviar correo de bienvenida con sus credenciales
            # _enviar_correo_bienvenida(paciente, password) 

            messages.success(request, f"Paciente {nombre} registrado con éxito.")
            return redirect("dentista:detalle_paciente", id=paciente.id)

        except Exception as e:
            messages.error(request, f"Error al registrar: {e}")
            # Si falló algo, podríamos borrar el usuario creado para no dejar basura, 
            # pero por ahora lo dejamos así para debugging.

    return render(request, "dentista/registrar_paciente.html", {"dentista": dentista})
@login_required
def editar_paciente(request, id):
    p = get_object_or_404(Paciente, id=id, dentista__user=request.user)
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        antecedentes = request.POST.get("antecedentes", "")
        fecha_nacimiento_raw = request.POST.get("fecha_nacimiento")

        if not (telefono_validado := _validar_telefono_10d(telefono)):
            messages.error(request, "El teléfono debe tener exactamente 10 dígitos numéricos.")
            p.nombre = nombre
            p.telefono = telefono
            p.direccion = direccion
            p.antecedentes = antecedentes
            return render(request, "dentista/editar_paciente.html", {"dentista": request.user.dentista, "paciente": p})
        if Paciente.objects.filter(dentista=request.user.dentista, telefono=telefono_validado).exclude(id=p.id).exists():
            messages.error(request, "Ya existe otro paciente con este teléfono.")
            p.nombre = nombre
            p.telefono = telefono
            p.direccion = direccion
            p.antecedentes = antecedentes
            return render(request, "dentista/editar_paciente.html", {"dentista": request.user.dentista, "paciente": p})
        if Paciente.objects.filter(dentista=request.user.dentista, nombre__iexact=nombre).exclude(id=p.id).exists():
            messages.error(request, "Ya existe otro paciente con ese nombre.")
            p.nombre = nombre
            p.telefono = telefono
            p.direccion = direccion
            p.antecedentes = antecedentes
            return render(request, "dentista/editar_paciente.html", {"dentista": request.user.dentista, "paciente": p})

        p.nombre = nombre
        p.telefono = telefono_validado
        p.direccion = direccion
        p.antecedentes = antecedentes
        if fecha_nacimiento_raw: 
            p.fecha_nacimiento = datetime.strptime(fecha_nacimiento_raw, "%Y-%m-%d").date()
        if request.FILES.get("imagen"): 
            p.imagen = request.FILES.get("imagen")
        p.save()
        return redirect("dentista:detalle_paciente", id=p.id)
    return render(request, "dentista/editar_paciente.html", {"dentista": request.user.dentista, "paciente": p})

@login_required
def detalle_paciente(request, id):
    p = get_object_or_404(Paciente, id=id, dentista__user=request.user)
    h = Cita.objects.filter(paciente=p).order_by("-fecha")
    tp = Pago.objects.filter(cita__paciente=p, estado="COMPLETADO").aggregate(Sum("monto"))["monto__sum"] or 0
    return render(request, "dentista/detalle_paciente.html", {"dentista": request.user.dentista, "paciente": p, "historial": h, "total_citas": h.count(), "total_pagado": tp})

@login_required
@require_POST
def eliminar_paciente(request, id):
    get_object_or_404(Paciente, id=id, dentista__user=request.user).delete()
    return redirect("dentista:pacientes")

@login_required
def odontograma_data(request, id):
    paciente = get_object_or_404(Paciente, id=id, dentista=request.user.dentista)
    dientes = Diente.objects.filter(paciente=paciente)
    data = [{"diente": d.numero, "estado": d.estado, "nota": d.nota or ""} for d in dientes]
    return JsonResponse(data, safe=False)

@login_required
def odontograma_guardar(request, id):
    if request.method == "POST":
        try:
            paciente = get_object_or_404(Paciente, id=id, dentista=request.user.dentista)
            body = json.loads(request.body)
            num = body.get('diente') or body.get('tooth')
            estado = body.get('estado') or body.get('status')
            nota = body.get('nota', '')

            if not num: return JsonResponse({'status': 'error', 'msg': 'Falta número'}, status=400)

            # Normalización
            if estado == 'ortodoncia': estado = 'bracket'
            if estado == 'restauracion': estado = 'caries'
            if estado == 'observacion': estado = 'corona'

            if estado == 'sano':
                Diente.objects.filter(paciente=paciente, numero=num).delete()
            else:
                Diente.objects.update_or_create(
                    paciente=paciente, numero=num,
                    defaults={'estado': estado, 'nota': nota}
                )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)


# ============================================================
#  7. PAGOS Y FACTURACIÓN
# ============================================================

@login_required
def pagos(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    if request.method == "POST": return redirect("dentista:registrar_pago")

    qs = Pago.objects.filter(cita__dentista=dentista).order_by("-created_at")
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    
    kpi_mes = qs.filter(created_at__date__gte=inicio_mes, estado="COMPLETADO").aggregate(Sum("monto"))["monto__sum"] or 0
    kpi_hoy = qs.filter(created_at__date=hoy, estado="COMPLETADO").aggregate(Sum("monto"))["monto__sum"] or 0
    kpi_efectivo = qs.filter(metodo="EFECTIVO", estado="COMPLETADO").aggregate(Sum("monto"))["monto__sum"] or 0
    kpi_digital = qs.filter(metodo__in=["TARJETA", "TRANSFERENCIA"], estado="COMPLETADO").aggregate(Sum("monto"))["monto__sum"] or 0
    kpi_total = qs.filter(estado="COMPLETADO").aggregate(Sum("monto"))["monto__sum"] or 0

    return render(request, "dentista/pagos.html", {
        "dentista": dentista, "pagos": qs,
        "kpi_mes": kpi_mes, "kpi_efectivo": kpi_efectivo,
        "kpi_digital": kpi_digital, "kpi_total": kpi_total,
        "kpi_hoy": kpi_hoy,
    })

@login_required
def registrar_pago(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    cita_preseleccionada = request.GET.get("cita_id") or request.POST.get("cita_id")
    base_citas = Cita.objects.filter(dentista=dentista)
    citas_pendientes = (
        base_citas.filter(
            Q(estado__in=["PENDIENTE", "CONFIRMADA"])
            | Q(pago_relacionado__estado="PENDIENTE")
        )
        | (base_citas.filter(id=cita_preseleccionada) if cita_preseleccionada else base_citas.none())
    ).distinct().order_by("fecha")

    if request.method == "POST":
        cita_id = request.POST.get("cita_id", "").strip()
        monto_raw = request.POST.get("monto", "").strip()
        concepto = request.POST.get("concepto", "").strip()
        metodo = request.POST.get("metodo", "EFECTIVO")
        
        try:
            monto_decimal = Decimal(monto_raw) if monto_raw else None
        except:
            messages.error(request, "Monto inválido")
            return redirect("dentista:registrar_pago")

        cita_obj = None
        if cita_id:
            cita_obj = get_object_or_404(Cita, id=cita_id, dentista=dentista)
            if not monto_decimal: monto_decimal = cita_obj.servicio.precio
            if not concepto: concepto = f"{cita_obj.servicio.nombre} - {cita_obj.paciente.nombre}"
        else:
            if not monto_decimal: 
                messages.error(request, "Ingresa un monto")
                return redirect("dentista:registrar_pago")
            # Venta mostrador (Paciente genérico)
            paciente_gen, _ = Paciente.objects.get_or_create(dentista=dentista, nombre="Venta Mostrador", defaults={"telefono": "000"})
            servicio_gen, _ = Servicio.objects.get_or_create(dentista=dentista, nombre="Pago Directo", defaults={"precio": 0, "duracion_estimada": 15})
            cita_obj = Cita.objects.create(dentista=dentista, paciente=paciente_gen, servicio=servicio_gen, fecha=date.today(), hora_inicio=timezone.localtime().time(), hora_fin=timezone.localtime().time(), estado="COMPLETADA", notas=concepto)

        pago_obj, _ = Pago.objects.update_or_create(cita=cita_obj, defaults={"monto": monto_decimal, "metodo": metodo, "estado": "COMPLETADO"})
        _reactivar_paciente_por_pago(pago_obj)
        
        if cita_obj.estado != "COMPLETADA":
            cita_obj.estado = "COMPLETADA"
            if not cita_obj.notas: cita_obj.notas = concepto
            cita_obj.save()

        _generar_comprobante_pdf(pago_obj)
        paciente_nombre = getattr(cita_obj.paciente, "nombre", "Paciente")
        fecha_txt = cita_obj.fecha.strftime("%d/%m") if getattr(cita_obj, "fecha", None) else ""
        hora_txt = cita_obj.hora_inicio.strftime("%H:%M") if getattr(cita_obj, "hora_inicio", None) else ""
        concepto_txt = concepto or getattr(getattr(cita_obj, "servicio", None), "nombre", "")
        horario_txt = f"{fecha_txt} {hora_txt}".strip()
        detalle_txt = " - ".join([p for p in [horario_txt, concepto_txt] if p])
        _guardar_aviso(
            dentista,
            " ".join(
                [
                    f"Pago registrado para {paciente_nombre}: ${pago_obj.monto}",
                    f"({pago_obj.metodo})",
                    f"- {detalle_txt}" if detalle_txt else "",
                ]
            ).strip(),
        )
        messages.success(request, "Pago registrado.")
        return redirect("dentista:pagos")

    return render(request, "dentista/registrar_pago.html", {
        "dentista": dentista,
        "citas": citas_pendientes,
        "cita_preseleccionada": cita_preseleccionada,
    })

@login_required
def descargar_comprobante(request, pago_id):
    """
    Genera (si no existe) y entrega el comprobante PDF del pago.
    """
    pago = get_object_or_404(
        Pago.objects.select_related("cita", "cita__dentista"),
        id=pago_id,
        cita__dentista__user=request.user,
    )

    # Regeneramos siempre para asegurar diseño y datos actualizados
    _generar_comprobante_pdf(pago)

    pdf_rel = None
    if getattr(pago, "comprobante", None):
        pdf_rel = (pago.comprobante.datos_extra or {}).get("pdf_path")

    if not pdf_rel:
        raise Http404("Comprobante no disponible.")

    pdf_path = Path(settings.MEDIA_ROOT) / pdf_rel
    if not pdf_path.exists():
        raise Http404("Archivo de comprobante no encontrado.")

    filename = pdf_path.name
    return FileResponse(
        open(pdf_path, "rb"),
        content_type="application/pdf",
        as_attachment=True,
        filename=filename,
    )

def _generar_comprobante_pdf(pago):
    """Genera PDF estilizado y lo guarda."""
    if not pago: return
    base_dir = Path(settings.MEDIA_ROOT)
    out_dir = base_dir / "comprobantes"
    out_dir.mkdir(parents=True, exist_ok=True)
    folio = f"RC-{pago.id:06d}"
    pdf_path = out_dir / f"{folio}.pdf"
    
    pdf_bytes = _pdf_recibo_lindo(pago, folio)
    pdf_path.write_bytes(pdf_bytes)
    
    ComprobantePago.objects.update_or_create(pago=pago, defaults={"folio": folio, "monto": pago.monto, "datos_extra": {"pdf_path": f"comprobantes/{folio}.pdf"}})

def _pdf_recibo_lindo(pago, folio):
    """
    Crea un PDF claro con bloques de información (sin librerías externas).
    """
    # Dimensiones carta
    width, height = 612, 792
    margin = 48

    # Helpers
    def esc(txt):
        return str(txt).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    def text(x, y, msg, size=12):
        return f"BT /F1 {size} Tf 0 0 0 rg {x} {y} Td ({esc(msg)}) Tj ET\n"
    def rect(x, y, w, h, fill=None, stroke=(0.8, 0.85, 0.95), sw=1):
        ops = ""
        if fill:
            r, g, b = fill
            ops += f"{r} {g} {b} rg "
        if stroke:
            r, g, b = stroke
            ops += f"{r} {g} {b} RG {sw} w "
        ops += f"{x} {y} {w} {h} re "
        if fill and stroke:
            ops += "B\n"
        elif fill:
            ops += "f\n"
        else:
            ops += "S\n"
        return ops

    # Datos
    cita = getattr(pago, "cita", None)
    paciente = getattr(cita, "paciente", None)
    dentista = getattr(cita, "dentista", None)
    servicio = getattr(cita, "servicio", None)
    fecha_cita = getattr(cita, "fecha", None)
    hora_cita = getattr(cita, "hora_inicio", None)
    duracion = getattr(servicio, "duracion_estimada", None)
    notas = getattr(cita, "notas", "") or ""
    fecha_pago = pago.created_at.strftime("%d/%m/%Y %H:%M")
    telefono_pac = getattr(paciente, "telefono", "") or "N/D"
    licencia = getattr(dentista, "licencia", "") or ""

    contenido = ""
    # Fondo tarjeta
    contenido += rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=(0.97, 0.99, 1), stroke=(0.77, 0.86, 0.95), sw=1.6)
    # Header
    header_h = 110
    contenido += rect(margin + 10, height - margin - header_h, width - 2 * margin - 20, header_h - 14, fill=(0.2, 0.38, 0.82), stroke=(0.2, 0.38, 0.82))
    contenido += text(margin + 24, height - margin - 36, "Consultorio Dental RC", 18)
    contenido += text(margin + 24, height - margin - 58, "Recibo de pago", 14)
    contenido += text(width - margin - 150, height - margin - 34, f"Folio: {folio}", 11)
    contenido += text(width - margin - 150, height - margin - 52, f"Emitido: {fecha_pago}", 11)

    # Bloque datos paciente / cita
    block_x = margin + 18
    block_y = height - margin - header_h - 240
    block_w = width - 2 * margin - 36
    block_h = 230
    contenido += rect(block_x, block_y, block_w, block_h, fill=(1, 1, 1), stroke=(0.75, 0.84, 0.95))
    y = block_y + block_h - 24
    contenido += text(block_x + 14, y, "Datos del paciente", 13); y -= 18
    contenido += text(block_x + 14, y, f"Nombre: {getattr(paciente, 'nombre', 'N/D')}", 12); y -= 16
    contenido += text(block_x + 14, y, f"Teléfono: {telefono_pac}", 12); y -= 22
    contenido += text(block_x + 14, y, "Dentista", 13); y -= 18
    contenido += text(block_x + 14, y, f"{getattr(dentista, 'nombre', 'Consultorio RC')} {('- ' + licencia) if licencia else ''}".strip(), 12); y -= 22
    contenido += text(block_x + 14, y, "Servicio", 13); y -= 18
    servicio_nom = getattr(servicio, "nombre", "Consulta / Pago")
    dur_txt = f" ({duracion} min)" if duracion else ""
    contenido += text(block_x + 14, y, f"{servicio_nom}{dur_txt}", 12); y -= 22
    fecha_label = fecha_cita.strftime("%d/%m/%Y") if fecha_cita else "N/D"
    hora_label = hora_cita.strftime("%H:%M") if hora_cita else ""
    contenido += text(block_x + 14, y, "Fecha de la cita", 13); y -= 18
    contenido += text(block_x + 14, y, f"{fecha_label} {hora_label}".strip(), 12)

    # Resumen de pago
    sum_h = 140
    sum_y = block_y - sum_h - 14
    contenido += rect(block_x, sum_y, block_w, sum_h, fill=(0.95, 0.98, 1), stroke=(0.75, 0.84, 0.95))
    contenido += text(block_x + 16, sum_y + sum_h - 30, "Monto", 12)
    contenido += text(block_x + 16, sum_y + sum_h - 56, f"${pago.monto:.2f} MXN", 18)
    contenido += text(block_x + 200, sum_y + sum_h - 30, "Método", 12)
    contenido += text(block_x + 200, sum_y + sum_h - 56, pago.metodo, 13)
    estado = (pago.estado or "COMPLETADO").title()
    contenido += text(block_x + 360, sum_y + sum_h - 30, "Estado", 12)
    contenido += text(block_x + 360, sum_y + sum_h - 56, estado, 13)
    if notas:
        contenido += text(block_x + 16, sum_y + 24, f"Concepto: {notas[:140]}", 11)

    # Pie de página
    contenido += text(margin + 6, margin + 32, "Gracias por tu pago. Conserva este recibo como comprobante. | Soporte: contacto@rc-dental.mx", 11)

    stream = contenido.encode("latin-1", "ignore")

    # Objetos PDF
    obj_catalog = b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    obj_pages = b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
    obj_page = b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >> endobj\n"
    obj_font = b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    obj_content = f"5 0 obj << /Length {len(stream)} >> stream\n".encode() + stream + b"\nendstream endobj\n"

    parts = [b"%PDF-1.4\n", obj_catalog, obj_pages, obj_page, obj_font, obj_content]
    offsets, cursor = [], 0
    for p in parts:
        offsets.append(cursor); cursor += len(p)
    xref_start = cursor

    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref_start).encode() + b"\n%%EOF"

    return b"".join(parts) + xref + trailer


# ============================================================
#  8. CONFIGURACIÓN, SOPORTE Y REPORTES
# ============================================================

@login_required
def configuracion(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_schedule":
            dia, h_ini, h_fin = request.POST.get("dia"), request.POST.get("hora_inicio"), request.POST.get("hora_fin")
            if dia and h_ini and h_fin:
                # Limpiamos duplicados previos y dejamos un solo bloque por día
                qs = Horario.objects.filter(dentista=dentista, dia_semana=int(dia))
                if qs.count() > 1:
                    qs.exclude(id=qs.first().id).delete()
                Horario.objects.update_or_create(
                    dentista=dentista,
                    dia_semana=int(dia),
                    defaults={"hora_inicio": h_ini, "hora_fin": h_fin},
                )
                messages.success(request, "Horario actualizado.")
        elif action == "update_profile":
            dentista.nombre = request.POST.get("nombre", dentista.nombre)
            dentista.telefono = request.POST.get("telefono", dentista.telefono)
            dentista.especialidad = request.POST.get("especialidad", dentista.especialidad)
            dentista.licencia = request.POST.get("licencia", dentista.licencia)
            if request.FILES.get("foto_perfil"): dentista.foto_perfil = request.FILES.get("foto_perfil")
            dentista.save()
            messages.success(request, "Perfil guardado.")
        elif action == "change_password":
            old, new, conf = request.POST.get("old_password"), request.POST.get("new_password"), request.POST.get("confirm_password")
            if new == conf and request.user.check_password(old):
                request.user.set_password(new)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Contraseña cambiada.")
            else:
                messages.error(request, "Error en contraseña.")
        return redirect("dentista:configuracion")

    return render(request, "dentista/configuracion.html", {"dentista": dentista, "dias_semana": Horario.DIAS, "horarios": Horario.objects.filter(dentista=dentista).order_by("dia_semana")})

@login_required
def eliminar_horario(request, id):
    get_object_or_404(Horario, id=id, dentista__user=request.user).delete()
    return redirect("dentista:configuracion")

@login_required
def soporte(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    if request.method == "POST":
        TicketSoporte.objects.create(dentista=dentista, asunto=request.POST.get("asunto"), mensaje=request.POST.get("mensaje"), estado="ABIERTO")
        try:
            enviar_correo_ticket_soporte(dentista, request.POST.get("asunto", ""), request.POST.get("mensaje", ""))
        except Exception as exc:
            print(f"[WARN] No se pudo enviar correo de soporte: {exc}")
        messages.success(request, "Ticket enviado.")
        return redirect("dentista:soporte")
    return render(request, "dentista/soporte.html", {"dentista": dentista, "tickets": TicketSoporte.objects.filter(dentista=dentista).order_by("-created_at")[:10]})

@login_required
def penalizaciones(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    # Lógica para mostrar logs de penalización si existen
    logs = PenalizacionLog.objects.filter(paciente__dentista=dentista).order_by("-created_at")[:20]
    pendientes = Pago.objects.filter(cita__dentista=dentista, estado="PENDIENTE")
    pacientes = Paciente.objects.filter(dentista=dentista).select_related("user").order_by("nombre")

    # Clasificamos pacientes por estado de penalización
    estado_grupos = {"penalizadas": [], "advertidas": [], "inhabilitadas": [], "activas": []}
    for p in pacientes:
        info = calcular_penalizacion_paciente(p, dentista)
        estado = info.get("estado")
        if not getattr(getattr(p, "user", None), "is_active", True) or estado == "disabled":
            grupo = "inhabilitadas"
        elif estado == "pending":
            # Tratamos pendiente (manual o automática) como advertida para mantenerla en esa columna
            grupo = "advertidas"
        elif estado == "warning":
            grupo = "advertidas"
        else:
            # Si tiene una advertencia manual, mantener en advertidas
            ultima_advertencia = (
                PenalizacionLog.objects.filter(paciente=p, accion="ADVERTENCIA")
                .order_by("-created_at")
                .first()
            )
            if ultima_advertencia:
                grupo = "advertidas"
            else:
                grupo = "activas"

        estado_grupos[grupo].append({"paciente": p, "info": info})
    
    # Procesar acciones manuales si se envían
    if request.method == "POST":
        accion = request.POST.get("accion")
        pid = request.POST.get("paciente_id")

        if accion in ("penalizar", "suspender", "reactivar", "advertencia"):
            if not pid:
                messages.error(request, "Indica el ID del paciente.")
                return redirect("dentista:penalizaciones")

            try:
                paciente = Paciente.objects.get(id=pid, dentista=dentista)
            except Paciente.DoesNotExist:
                messages.error(request, "Paciente no encontrado para este dentista.")
                return redirect("dentista:penalizaciones")

            if accion == "penalizar":
                cita = Cita.objects.filter(paciente=paciente).order_by("-fecha", "-hora_inicio").first()
                if not cita:
                    messages.error(request, "El paciente no tiene citas para registrar inasistencia.")
                else:
                    msg = procesar_inasistencia(cita) or "Inasistencia registrada."
                    messages.success(request, f"Penalización aplicada a {paciente.nombre}. {msg}")

            elif accion == "suspender":
                usuario = getattr(paciente, "user", None)
                if not usuario:
                    messages.error(request, "El paciente no tiene usuario vinculado para suspender.")
                else:
                    if usuario.is_active:
                        usuario.is_active = False
                        usuario.save(update_fields=["is_active"])
                    PenalizacionLog.objects.create(
                        dentista=dentista,
                        paciente=paciente,
                        accion="SUSPENDER",
                        motivo="Suspensión manual aplicada por el dentista.",
                        monto=Decimal("0"),
                    )
                    messages.success(request, f"Cuenta de {paciente.nombre} suspendida.")

            elif accion == "reactivar":
                usuario = getattr(paciente, "user", None)
                if not usuario:
                    messages.error(request, "El paciente no tiene usuario vinculado para reactivar.")
                else:
                    if not usuario.is_active:
                        usuario.is_active = True
                        usuario.save(update_fields=["is_active"])
                    PenalizacionLog.objects.create(
                        dentista=dentista,
                        paciente=paciente,
                        accion="REACTIVAR",
                        motivo="Reactivación manual aplicada por el dentista.",
                        monto=Decimal("0"),
                    )
                    messages.success(request, f"Cuenta de {paciente.nombre} reactivada.")

            elif accion == "advertencia":
                # Generamos pago pendiente de penalización ($300) y mantenemos en advertidas
                cita = (
                    Cita.objects.filter(paciente=paciente)
                    .order_by("-fecha", "-hora_inicio")
                    .first()
                )
                if not cita:
                    servicio_base = (
                        Servicio.objects.filter(dentista=dentista)
                        .order_by("id")
                        .first()
                    )
                    if not servicio_base:
                        messages.error(request, "Configura al menos un servicio para aplicar advertencias.")
                        return redirect("dentista:penalizaciones")
                    ahora = timezone.localtime()
                    cita = Cita.objects.create(
                        dentista=dentista,
                        paciente=paciente,
                        servicio=servicio_base,
                        fecha=ahora.date(),
                        hora_inicio=ahora.time(),
                        hora_fin=(ahora + timedelta(minutes=30)).time(),
                        estado="INASISTENCIA",
                        notas="Penalización manual: advertencia con cargo.",
                    )
                else:
                    if cita.estado != "INASISTENCIA":
                        cita.estado = "INASISTENCIA"
                        cita.save(update_fields=["estado"])

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
                    dentista=dentista,
                    paciente=paciente,
                    accion="ADVERTENCIA",
                    motivo="Advertencia aplicada: debe pagar $300 para reactivar citas.",
                    monto=Decimal("300.00"),
                )
                # Notificar al paciente por correo si tiene email
                correo_paciente = getattr(getattr(paciente, "user", None), "email", None)
                if correo_paciente:
                    try:
                        enviar_correo_penalizacion(
                            email_destino=correo_paciente,
                            nombre_paciente=paciente.nombre,
                            motivo="Advertencia aplicada: debes cubrir $300 para reactivar tus citas.",
                            recargo=300,
                            dias_limite=5,
                        )
                    except Exception as exc:
                        print(f"[WARN] No se pudo enviar correo de advertencia: {exc}")
                # Si acumula 2 o más advertencias, desactivar cuenta automáticamente
                advert_count = PenalizacionLog.objects.filter(paciente=paciente, accion="ADVERTENCIA").count()
                if advert_count >= 2:
                    usuario = getattr(paciente, "user", None)
                    if usuario and usuario.is_active:
                        usuario.is_active = False
                        usuario.save(update_fields=["is_active"])
                    PenalizacionLog.objects.create(
                        dentista=dentista,
                        paciente=paciente,
                        accion="SUSPENDER",
                        motivo="Cuenta inhabilitada automáticamente por reincidencia de advertencias.",
                        monto=Decimal("0"),
                    )
                    messages.warning(
                        request,
                        f"{paciente.nombre} alcanzó {advert_count} advertencias y fue inhabilitado automáticamente.",
                    )
                else:
                    messages.success(
                        request,
                        f"Advertencia registrada para {paciente.nombre}. Pago pendiente de $300 y agenda bloqueada.",
                    )

            return redirect("dentista:penalizaciones")

        messages.info(request, "Acción no reconocida.")

    return render(request, "dentista/penalizaciones.html", {
        "dentista": dentista,
        "logs": logs,
        "pendientes": pendientes,
        "pacientes": pacientes,
        "estado_grupos": estado_grupos,
    })

@login_required
def reportes(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    hoy = timezone.localdate()
    fi = datetime.strptime(request.GET.get("inicio") or (hoy - timedelta(30)).strftime("%Y-%m-%d"), "%Y-%m-%d").date()
    ff = datetime.strptime(request.GET.get("fin") or hoy.strftime("%Y-%m-%d"), "%Y-%m-%d").date()
    citas = (
        Cita.objects.filter(dentista=dentista, fecha__range=(fi, ff))
        .select_related("paciente", "servicio")
        .prefetch_related("encuestasatisfaccion_set")
        .order_by("-fecha")
    )
    pagos = (
        Pago.objects.filter(cita__dentista=dentista, created_at__date__range=(fi, ff))
        .select_related("cita", "cita__paciente", "cita__servicio")
        .order_by("-created_at")
    )
    total_cobrado = pagos.filter(estado="COMPLETADO").aggregate(Sum("monto"))["monto__sum"] or 0
    return render(request, "dentista/reportes.html", {
        "dentista": dentista, "citas": citas, "fecha_inicio": fi, "fecha_fin": ff,
        "total_monto": total_cobrado,
        "total_citas": citas.count(),
        "total_pacientes": citas.values("paciente_id").distinct().count(),
        "pagos": pagos,
    })

@login_required
def reporte_csv(request):
    # Generación simple de CSV
    dentista = get_object_or_404(Dentista, user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte.csv"'
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Paciente', 'Servicio', 'Monto'])
    for c in Cita.objects.filter(dentista=dentista):
        monto = c.pago_relacionado.monto if hasattr(c, 'pago_relacionado') else 0
        writer.writerow([c.fecha, c.paciente.nombre, c.servicio.nombre, monto])
    return response

@login_required
def reporte_pdf(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    hoy = timezone.localdate()
    fi = datetime.strptime(
        request.GET.get("inicio") or (hoy - timedelta(30)).strftime("%Y-%m-%d"),
        "%Y-%m-%d",
    ).date()
    ff = datetime.strptime(
        request.GET.get("fin") or hoy.strftime("%Y-%m-%d"),
        "%Y-%m-%d",
    ).date()
    citas = (
        Cita.objects.filter(dentista=dentista, fecha__range=(fi, ff))
        .select_related("paciente", "servicio")
        .order_by("fecha", "hora_inicio")
    )
    pagos = (
        Pago.objects.filter(cita__dentista=dentista, created_at__date__range=(fi, ff))
        .select_related("cita", "cita__paciente", "cita__servicio")
        .order_by("-created_at")
    )

    total_monto = pagos.filter(estado="COMPLETADO").aggregate(Sum("monto"))["monto__sum"] or 0
    total_pendiente = pagos.filter(estado="PENDIENTE").aggregate(Sum("monto"))["monto__sum"] or 0
    total_citas = citas.count()
    total_pacientes = citas.values("paciente_id").distinct().count()

    def esc(txt):
        return str(txt).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def rect(x, y, w, h, fill=None, stroke=(0.8, 0.85, 0.95), sw=1):
        ops = ""
        if fill:
            r, g, b = fill
            ops += f"{r} {g} {b} rg "
        if stroke:
            r, g, b = stroke
            ops += f"{r} {g} {b} RG {sw} w "
        ops += f"{x} {y} {w} {h} re "
        if fill and stroke:
            ops += "B\n"
        elif fill:
            ops += "f\n"
        else:
            ops += "S\n"
        return ops

    def text(x, y, msg, size=12):
        return f"BT /F1 {size} Tf 0 0 0 rg {x} {y} Td ({esc(msg)}) Tj ET\n"

    width, height = 595, 842
    margin = 40
    contenido = ""

    # Fondo principal
    contenido += rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=(0.97, 0.99, 1), stroke=(0.77, 0.86, 0.95), sw=1.4)

    # Header
    header_h = 120
    contenido += rect(margin + 8, height - margin - header_h, width - 2 * margin - 16, header_h - 12, fill=(0.2, 0.4, 0.82), stroke=(0.2, 0.4, 0.82))
    contenido += text(margin + 22, height - margin - 40, "Reporte de citas y pagos", 18)
    contenido += text(margin + 22, height - margin - 62, f"Dentista: {dentista.nombre}", 12)
    contenido += text(margin + 22, height - margin - 82, f"Rango: {fi.strftime('%d/%m/%Y')} - {ff.strftime('%d/%m/%Y')}", 12)
    contenido += text(width - margin - 160, height - margin - 40, f"Citas: {total_citas}", 12)
    contenido += text(width - margin - 160, height - margin - 58, f"Pacientes: {total_pacientes}", 12)
    contenido += text(width - margin - 160, height - margin - 76, f"Cobrado: ${total_monto:.2f}", 12)
    contenido += text(width - margin - 160, height - margin - 94, f"Pendiente: ${total_pendiente:.2f}", 12)

    # Subheader tabla
    table_top = height - margin - header_h - 30
    contenido += rect(margin + 8, table_top - 26, width - 2 * margin - 16, 28, fill=(0.9, 0.95, 1), stroke=(0.75, 0.84, 0.95))
    headers = [
        ("FECHA", margin + 16),
        ("HORA", margin + 90),
        ("PACIENTE", margin + 150),
        ("SERVICIO", margin + 300),
        ("MONTO", width - margin - 90),
    ]
    for h_label, hx in headers:
        contenido += text(hx, table_top - 8, h_label, 11)

    # Filas
    y = table_top - 40
    max_rows = 20
    row = 0
    for c in citas:
        if row >= max_rows:
            break  # corte simple
        monto = getattr(getattr(c, "pago_relacionado", None), "monto", None)
        monto_txt = f"${monto:.2f}" if monto else "-"
        contenido += text(margin + 16, y, c.fecha.strftime("%d/%m/%Y"), 10)
        contenido += text(margin + 90, y, c.hora_inicio.strftime("%H:%M"), 10)
        contenido += text(margin + 150, y, c.paciente.nombre[:26], 10)
        contenido += text(margin + 300, y, c.servicio.nombre[:22], 10)
        contenido += text(width - margin - 90, y, monto_txt, 10)
        y -= 18
        row += 1

    # Espacio y tabla de pagos
    y -= 20
    contenido += rect(margin + 8, y, width - 2 * margin - 16, 24, fill=(0.9, 0.95, 1), stroke=(0.75, 0.84, 0.95))
    contenido += text(margin + 16, y + 6, "PAGOS (incluye pendientes)", 11)
    y -= 18

    pagos_headers = [
        ("FECHA", margin + 16),
        ("PACIENTE", margin + 110),
        ("MÉTODO", margin + 280),
        ("ESTADO", margin + 370),
        ("MONTO", width - margin - 90),
    ]
    for label, hx in pagos_headers:
        contenido += text(hx, y, label, 11)
    y -= 16

    max_pagos = 14
    for p in pagos[:max_pagos]:
        if y < margin + 40:
            break
        contenido += text(margin + 16, y, p.created_at.strftime("%d/%m/%Y"), 10)
        contenido += text(margin + 110, y, p.cita.paciente.nombre[:26], 10)
        contenido += text(margin + 280, y, p.metodo[:14], 10)
        contenido += text(margin + 370, y, p.estado[:12], 10)
        contenido += text(width - margin - 90, y, f"${p.monto:.2f}", 10)
        y -= 16

    # Nota pie
    contenido += text(margin + 4, margin + 28, "Generado automáticamente por RC Dental. Para detalles completos exporta el CSV.", 10)

    stream = contenido.encode("latin-1", "ignore")

    obj_catalog = b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    obj_pages = b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
    obj_page = b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >> endobj\n"
    obj_font = b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    obj_content = f"5 0 obj << /Length {len(stream)} >> stream\n".encode() + stream + b"\nendstream endobj\n"

    parts = [b"%PDF-1.4\n", obj_catalog, obj_pages, obj_page, obj_font, obj_content]
    offsets, cursor = [], 0
    for p in parts:
        offsets.append(cursor); cursor += len(p)
    xref_start = cursor

    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref_start).encode() + b"\n%%EOF"

    pdf_bytes = b"".join(parts) + xref + trailer
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reporte.pdf"'
    return response
