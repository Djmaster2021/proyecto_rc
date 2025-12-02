# ============================================================
#  VIEWS DEL DENTISTA — SISTEMA RC DENTAL PRO (PARTE 1)
# ============================================================

from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from domain.models import (
    AvisoDentista,
    Cita,
    Dentista,
    Horario,
    Paciente,
    Pago,
    Servicio,
)

# ============================================================
# FUNCIÓN IA: Riesgo de Inasistencia
# ============================================================

def calcular_riesgo_paciente(paciente):
    citas = Cita.objects.filter(paciente=paciente)
    faltas = citas.filter(estado="INASISTENCIA").count()
    reprogramaciones = max(citas.count() - 1, 0)
    pagos_pend = Pago.objects.filter(cita__paciente=paciente, estado="PENDIENTE").count()

    riesgo = (faltas * 0.5) + (reprogramaciones * 0.3) + (pagos_pend * 0.2)
    riesgo_percent = min(int(riesgo * 20), 100)

    if riesgo_percent >= 70:
        nivel, color = "Alto", "badge-red"
    elif riesgo_percent >= 35:
        nivel, color = "Medio", "badge-yellow"
    else:
        nivel, color = "Bajo", "badge-green"

    return {"paciente": paciente.nombre, "porcentaje": riesgo_percent, "nivel": nivel, "color": color}

# ============================================================
# FUNCIÓN IA: Optimización
# ============================================================

def optimizar_agenda(citas_dia):
    sugerencias = []
    citas_orden = sorted(citas_dia, key=lambda x: x.hora_inicio)
    for i in range(len(citas_orden) - 1):
        fin = datetime.combine(citas_orden[i].fecha, citas_orden[i].hora_fin)
        inicio_next = datetime.combine(citas_orden[i + 1].fecha, citas_orden[i + 1].hora_inicio)
        gap = (inicio_next - fin).seconds // 60
        if gap >= 20:
            sugerencias.append(f"Hueco de {gap} min entre {citas_orden[i].paciente.nombre} y {citas_orden[i + 1].paciente.nombre}.")
    return sugerencias

# ============================================================
# DASHBOARD PRINCIPAL (Con limpieza visual de citas pasadas)
# ============================================================

@login_required
def dashboard_dentista(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    hoy = date.today()
    ahora = timezone.localtime()
    hora_actual = ahora.time()

    # --- Citas de hoy (Para IA y contadores) ---
    citas_hoy_query = Cita.objects.filter(dentista=dentista, fecha=hoy).exclude(estado__in=["CANCELADA", "INASISTENCIA"])
    citas_hoy = citas_hoy_query.order_by("hora_inicio")

    # --- KPIs ---
    kpi_pacientes = Paciente.objects.filter(dentista=dentista).count()
    kpi_pendientes = Cita.objects.filter(dentista=dentista, estado="PENDIENTE").count()
    inicio_mes = hoy.replace(day=1)
    ingresos_mes = Pago.objects.filter(cita__dentista=dentista, estado="COMPLETADO", created_at__date__gte=inicio_mes).aggregate(Sum("monto"))["monto__sum"] or 0

    # --- Próxima Cita (Lógica Inteligente) ---
    # Solo muestra citas futuras o presentes. Las pasadas se ocultan.
    proxima_cita = Cita.objects.filter(
        dentista=dentista,
        estado__in=["PENDIENTE", "CONFIRMADA"]
    ).filter(
        Q(fecha__gt=hoy) | Q(fecha=hoy, hora_fin__gt=hora_actual)
    ).order_by("fecha", "hora_inicio").first()

    # --- Radar Operativo (Calendario con Limpieza Visual) ---
    if inicio_mes.month == 12: inicio_next = inicio_mes.replace(year=inicio_mes.year+1, month=1, day=1)
    else: inicio_next = inicio_mes.replace(month=inicio_mes.month+1, day=1)
    
    calendario_dias = []
    for i in range((inicio_next - inicio_mes).days):
        fecha = inicio_mes + timedelta(days=i)
        citas_dia = Cita.objects.filter(dentista=dentista, fecha=fecha)
        
        citas_procesadas = []
        for c in citas_dia:
            # MAGIA VISUAL: Si la cita ya pasó, le ponemos clase 'pasada'
            # para ocultarla o atenuarla en el CSS, aunque siga en base de datos.
            es_pasada = (fecha < hoy) or (fecha == hoy and c.hora_fin < hora_actual)
            
            # Si quieres que DESAPAREZCAN del radar, descomenta la siguiente línea:
            # if es_pasada: continue 
            
            clase_estado = "cita-pasada" if es_pasada else c.estado.lower()
            citas_procesadas.append({
                "paciente": c.paciente.nombre,
                "hora": c.hora_inicio.strftime("%H:%M"),
                "clase_estado": clase_estado
            })

        calendario_dias.append({
            "dia": fecha,
            "label_dia": fecha.strftime("%a"),
            "clases": "hoy" if fecha == hoy else "",
            "citas": citas_procesadas
        })

    # --- IA y Gráficas ---
    riesgos = [calcular_riesgo_paciente(p) for p in Paciente.objects.filter(dentista=dentista)]
    sugerencias = optimizar_agenda(citas_hoy)
    
    data_diarios = []
    labels_diarios = []
    for i in range(6, -1, -1):
        f = hoy - timedelta(days=i)
        labels_diarios.append(f.strftime("%d/%m"))
        data_diarios.append(Cita.objects.filter(dentista=dentista, fecha=f).exclude(estado__in=["CANCELADA", "INASISTENCIA"]).count())

    return render(request, "dentista/dashboard.html", {
        "dentista": dentista, "citas_hoy": citas_hoy, "kpi_pacientes": kpi_pacientes,
        "kpi_pendientes": kpi_pendientes, "ingresos_mes": ingresos_mes, "proxima_cita": proxima_cita,
        "notificaciones": AvisoDentista.objects.filter(dentista=dentista).order_by("-created_at")[:10],
        "calendario_dias": calendario_dias, "riesgos": riesgos, "sugerencias": sugerencias,
        "labels_diarios": labels_diarios, "data_diarios": data_diarios,
        "pagos": Pago.objects.filter(cita__dentista=dentista).order_by("-created_at")[:5]
    })

# ============================================================
# AGENDA MULTISEMANAL (Con limpieza visual)
# ============================================================

@login_required
def agenda_dentista(request, modo=None):
    dentista = get_object_or_404(Dentista, user=request.user)
    hoy = date.today()
    hora_actual = timezone.localtime().time()
    inicio = hoy - timedelta(days=hoy.weekday())
    semanas = []

    for w in range(4):
        semana = []
        for d in range(7):
            fecha = inicio + timedelta(days=(w * 7) + d)
            citas = Cita.objects.filter(fecha=fecha)
            citas_info = []
            
            for c in citas:
                # LÓGICA DE LIMPIEZA:
                # Si la cita ya pasó (hora fin < hora actual), marcamos visualmente
                es_pasada = (fecha < hoy) or (fecha == hoy and c.hora_fin < hora_actual)
                
                estado_visual = "FINALIZADA" if es_pasada else c.estado
                clase_extra = "ghost-mode" if es_pasada else ""

                citas_info.append({
                    "obj": c,
                    "es_mia": (c.dentista == dentista),
                    "dentista_nombre": c.dentista.nombre,
                    "estado_visual": estado_visual, # Para mostrar "Finalizada" en texto
                    "clase_extra": clase_extra      # Para CSS (opacidad/ocultar)
                })

            semana.append({
                "fecha": fecha,
                "tipo_dia": "laboral" if Horario.objects.filter(dentista=dentista, dia_semana=fecha.isoweekday()).exists() else "descanso",
                "citas": citas_info,
            })
        semanas.append(semana)

    return render(request, "dentista/agenda.html", {
        "dentista": dentista, "semanas": semanas, "fecha_actual": hoy,
    })

# ============================================================
#  VIEWS DEL DENTISTA — PARTE 2
# ============================================================

def obtener_horas_disponibles(dentista, fecha, duracion):
    horarios = Horario.objects.filter(dentista=dentista, dia_semana=fecha.isoweekday())
    if not horarios: return []
    ocupados = [(datetime.combine(fecha, c.hora_inicio), datetime.combine(fecha, c.hora_fin)) for c in Cita.objects.filter(dentista=dentista, fecha=fecha)]
    
    horas_libres = []
    for h in horarios:
        cursor = datetime.combine(fecha, h.hora_inicio)
        fin_jornada = datetime.combine(fecha, h.hora_fin)
        while cursor + timedelta(minutes=duracion) <= fin_jornada:
            slot_fin = cursor + timedelta(minutes=duracion)
            if not any(cursor < o_fin and slot_fin > o_inicio for o_inicio, o_fin in ocupados):
                horas_libres.append(cursor.strftime("%H:%M"))
            cursor += timedelta(minutes=30)
    return horas_libres

@login_required
def crear_cita_manual(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    
    # Rango de fechas: Hoy hasta 2 meses (60 días)
    hoy = date.today()
    limite = hoy + timedelta(days=60)
    
    if request.method == "POST":
        # ... (TU CÓDIGO POST SE MANTIENE IGUAL, SOLO ASEGURA RECIBIR 'hora') ...
        # Aquí procesas el guardado como ya lo tenías
        paciente_id = request.POST.get("paciente")
        servicio_id = request.POST.get("servicio")
        fecha_str = request.POST.get("fecha")
        hora_str = request.POST.get("hora") # Ahora vendrá de un select/botón

        # (Pega aquí tu lógica de validación y guardado del POST anterior)
        # Solo asegúrate de recalcular hora_fin basado en el servicio:
        servicio = get_object_or_404(Servicio, id=servicio_id)
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hora_inicio = datetime.strptime(hora_str, "%H:%M").time()
        hora_fin = (datetime.combine(fecha, hora_inicio) + timedelta(minutes=servicio.duracion_estimada)).time()
        
        Cita.objects.create(
            dentista=dentista, paciente_id=paciente_id, servicio=servicio,
            fecha=fecha, hora_inicio=hora_inicio, hora_fin=hora_fin, estado="PENDIENTE"
        )
        messages.success(request, "Cita agendada correctamente.")
        return redirect("dentista:agenda")

    return render(request, "dentista/crear_cita_manual.html", {
        "dentista": dentista,
        "pacientes": Paciente.objects.filter(dentista=dentista),
        "servicios": Servicio.objects.filter(dentista=dentista),
        
        # VARIABLES NUEVAS PARA LOS LÍMITES DE FECHA
        "fecha_min": hoy.strftime("%Y-%m-%d"),
        "fecha_max": limite.strftime("%Y-%m-%d"),
    })

@login_required
@require_POST
def eliminar_cita(request, id):
    c = get_object_or_404(Cita, id=id, dentista__user=request.user)
    c.delete()
    messages.success(request, "Cita eliminada.")
    return redirect("dentista:agenda")

@login_required
def consulta(request, id):
    c = get_object_or_404(Cita, id=id, dentista__user=request.user)
    if request.method == "POST":
        c.notas = request.POST.get("notas_clinicas", "")
        if request.FILES.get("archivo_adjunto"): c.archivo_adjunto = request.FILES.get("archivo_adjunto")
        
        pagado = "pagado" in request.POST
        if pagado:
            c.estado = "COMPLETADA"
            Pago.objects.update_or_create(cita=c, defaults={"monto": request.POST.get("monto", c.servicio.precio), "estado": "COMPLETADO", "metodo": "EFECTIVO"})
        else:
            if c.estado not in ["COMPLETADA", "CANCELADA"]: c.estado = "CONFIRMADA"
        c.save()
        messages.success(request, "Expediente actualizado.")
        return redirect("dentista:consulta", id=c.id)
    
    return render(request, "dentista/consulta.html", {"dentista": c.dentista, "cita": c, "pago": getattr(c, 'pago_relacionado', None)})

@login_required
def pacientes(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    qs = Paciente.objects.filter(dentista=dentista).order_by("nombre")
    q = request.GET.get("q", "").strip()
    if q: qs = qs.filter(Q(nombre__icontains=q) | Q(telefono__icontains=q))
    return render(request, "dentista/pacientes.html", {"dentista": dentista, "pacientes": qs, "query": q})

# Vistas simples restantes
@login_required
def pagos(request):
    return render(request, "dentista/pagos.html", {"dentista": request.user.dentista, "pagos": Pago.objects.filter(cita__dentista=request.user.dentista).order_by("-created_at")})

@login_required
def reportes(request): return render(request, "dentista/reportes.html", {"dentista": request.user.dentista})

@login_required
def servicios(request): return render(request, "dentista/servicios.html", {"dentista": request.user.dentista, "servicios": Servicio.objects.filter(dentista=request.user.dentista)})

@login_required
def penalizaciones(request): return render(request, "dentista/penalizaciones.html", {"dentista": request.user.dentista, "pendientes": Pago.objects.filter(cita__dentista=request.user.dentista, estado="PENDIENTE")})

@login_required
def configuracion(request):
    d = request.user.dentista
    if request.method == "POST":
        d.nombre = request.POST.get("nombre", d.nombre)
        d.telefono = request.POST.get("telefono", d.telefono)
        d.especialidad = request.POST.get("especialidad", d.especialidad)
        d.licencia = request.POST.get("licencia", d.licencia)
        d.save()
        messages.success(request, "Datos guardados.")
    return render(request, "dentista/configuracion.html", {"dentista": d})

@login_required
def soporte(request): return render(request, "dentista/soporte.html", {"dentista": request.user.dentista})

@login_required
def detalle_paciente(request, id):
    p = get_object_or_404(Paciente, id=id, dentista__user=request.user)
    h = Cita.objects.filter(paciente=p).order_by("-fecha")
    tp = Pago.objects.filter(cita__paciente=p, estado="COMPLETADO").aggregate(Sum("monto"))["monto__sum"] or 0
    if not hasattr(p, "genero"): setattr(p, "genero", "No especificado")
    return render(request, "dentista/detalle_paciente.html", {"dentista": request.user.dentista, "paciente": p, "historial": h, "total_citas": h.count(), "total_pagado": tp})

@login_required
def registrar_paciente(request):
    if request.method == "POST":
        p = Paciente.objects.create(dentista=request.user.dentista, nombre=request.POST.get("nombre"), telefono=request.POST.get("telefono"), direccion=request.POST.get("direccion"), antecedentes=request.POST.get("antecedentes"))
        if request.POST.get("fecha_nacimiento"): p.fecha_nacimiento = datetime.strptime(request.POST.get("fecha_nacimiento"), "%Y-%m-%d").date(); p.save()
        return redirect("dentista:detalle_paciente", id=p.id)
    return render(request, "dentista/registrar_paciente.html", {"dentista": request.user.dentista})

@login_required
def editar_paciente(request, id):
    p = get_object_or_404(Paciente, id=id, dentista__user=request.user)
    if request.method == "POST":
        p.nombre = request.POST.get("nombre")
        p.telefono = request.POST.get("telefono")
        p.direccion = request.POST.get("direccion")
        p.antecedentes = request.POST.get("antecedentes")
        if request.POST.get("fecha_nacimiento"): p.fecha_nacimiento = datetime.strptime(request.POST.get("fecha_nacimiento"), "%Y-%m-%d").date()
        p.save()
        return redirect("dentista:detalle_paciente", id=p.id)
    return render(request, "dentista/editar_paciente.html", {"dentista": request.user.dentista, "paciente": p})

@login_required
def obtener_slots_disponibles(request):
    """
    API interna llamada por JS para obtener horas disponibles
    basadas en la duración exacta del servicio.
    """
    dentista = get_object_or_404(Dentista, user=request.user)
    
    fecha_str = request.GET.get('fecha')
    servicio_id = request.GET.get('servicio_id')

    if not fecha_str or not servicio_id:
        return JsonResponse({'slots': []})

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        servicio = Servicio.objects.get(id=servicio_id)
        duracion = servicio.duracion_estimada
    except (ValueError, Servicio.DoesNotExist):
        return JsonResponse({'slots': []})

    # Validar día laboral
    horarios = Horario.objects.filter(dentista=dentista, dia_semana=fecha.isoweekday())
    if not horarios.exists():
        return JsonResponse({'slots': [], 'mensaje': 'Día no laboral'})

    # Obtener citas existentes para bloquear rangos
    citas = Cita.objects.filter(dentista=dentista, fecha=fecha).exclude(estado__in=['CANCELADA', 'INASISTENCIA'])
    ocupados = []
    for c in citas:
        inicio = datetime.combine(fecha, c.hora_inicio)
        fin = datetime.combine(fecha, c.hora_fin)
        ocupados.append((inicio, fin))

    slots_disponibles = []
    
    # Lógica de cálculo de huecos
    for h in horarios:
        inicio_jornada = datetime.combine(fecha, h.hora_inicio)
        fin_jornada = datetime.combine(fecha, h.hora_fin)
        
        cursor = inicio_jornada
        
        # Iteramos cada 15 minutos buscando huecos del tamaño del servicio
        while cursor + timedelta(minutes=duracion) <= fin_jornada:
            slot_inicio = cursor
            slot_fin = cursor + timedelta(minutes=duracion)
            
            # Verificamos colisión
            colision = False
            for o_inicio, o_fin in ocupados:
                # Si el slot empieza antes de que termine otra Y termina después de que empiece otra
                if slot_inicio < o_fin and slot_fin > o_inicio:
                    colision = True
                    break
            
            if not colision:
                # Filtrar horas pasadas si es hoy
                ahora = datetime.now()
                if fecha == date.today() and slot_inicio < ahora:
                    pass # Ya pasó esta hora
                else:
                    slots_disponibles.append({
                        'hora': slot_inicio.strftime("%H:%M"),
                        'fin': slot_fin.strftime("%H:%M"),
                        'recomendado': False # Se calcula abajo
                    })
            
            cursor += timedelta(minutes=15) # Saltos de 15 min

    # "IA" Simple: Recomendar el primero disponible (más cercano)
    if slots_disponibles:
        slots_disponibles[0]['recomendado'] = True

    return JsonResponse({'slots': slots_disponibles})


@login_required
@require_POST
def eliminar_paciente(request, id):
    dentista = get_object_or_404(Dentista, user=request.user)
    paciente = get_object_or_404(Paciente, id=id, dentista=dentista)
    
    # Opcional: Validar si tiene historial crítico
    # if Pago.objects.filter(cita__paciente=paciente).exists():
    #     messages.error(request, "No se puede eliminar: El paciente tiene historial financiero.")
    #     return redirect("dentista:pacientes")

    nombre = paciente.nombre
    paciente.delete()
    messages.success(request, f"Paciente {nombre} eliminado correctamente.")
    return redirect("dentista:pacientes")