# ============================================================
#  VIEWS DEL DENTISTA — SISTEMA RC DENTAL PRO (FINAL)
# ============================================================

import json
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

# IMPORTAMOS TODOS LOS MODELOS NECESARIOS
from domain.models import (
    AvisoDentista,
    Cita,
    Dentista,
    Horario,
    Paciente,
    Pago,
    Servicio,
    Diente, # <--- Importante
)

# ... (Funciones de IA: calcular_riesgo_paciente y optimizar_agenda se quedan igual) ...
def calcular_riesgo_paciente(paciente):
    citas = Cita.objects.filter(paciente=paciente)
    riesgo = (citas.filter(estado="INASISTENCIA").count() * 0.5) + \
             (max(citas.count() - 1, 0) * 0.3) + \
             (Pago.objects.filter(cita__paciente=paciente, estado="PENDIENTE").count() * 0.2)
    riesgo_percent = min(int(riesgo * 20), 100)
    if riesgo_percent >= 70: lvl, col = "Alto", "badge-red"
    elif riesgo_percent >= 35: lvl, col = "Medio", "badge-yellow"
    else: lvl, col = "Bajo", "badge-green"
    return {"paciente": paciente.nombre, "porcentaje": riesgo_percent, "nivel": lvl, "color": col}

def optimizar_agenda(citas_dia):
    sugerencias = []
    citas = sorted(citas_dia, key=lambda x: x.hora_inicio)
    for i in range(len(citas) - 1):
        fin = datetime.combine(citas[i].fecha, citas[i].hora_fin)
        ini = datetime.combine(citas[i+1].fecha, citas[i+1].hora_inicio)
        if (ini - fin).seconds // 60 >= 20:
            sugerencias.append(f"Hueco libre entre {citas[i].paciente.nombre} y {citas[i+1].paciente.nombre}.")
    return sugerencias

# ============================================================
# DASHBOARD
# ============================================================
@login_required
def dashboard_dentista(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    hoy = date.today()
    hora_actual = timezone.localtime().time()

    citas_hoy = Cita.objects.filter(dentista=dentista, fecha=hoy).exclude(estado__in=["CANCELADA", "INASISTENCIA"]).order_by("hora_inicio")
    inicio_mes = hoy.replace(day=1)
    
    # KPIs
    kpi_pacs = Paciente.objects.filter(dentista=dentista).count()
    kpi_pend = Cita.objects.filter(dentista=dentista, estado="PENDIENTE").count()
    ingresos = Pago.objects.filter(cita__dentista=dentista, estado="COMPLETADO", created_at__date__gte=inicio_mes).aggregate(Sum("monto"))["monto__sum"] or 0

    # Próxima Cita
    prox = Cita.objects.filter(dentista=dentista, estado__in=["PENDIENTE", "CONFIRMADA"]).filter(Q(fecha__gt=hoy)|Q(fecha=hoy, hora_fin__gt=hora_actual)).order_by("fecha", "hora_inicio").first()

    # Radar
    if inicio_mes.month == 12: sig = inicio_mes.replace(year=inicio_mes.year+1, month=1, day=1)
    else: sig = inicio_mes.replace(month=inicio_mes.month+1, day=1)
    
    calendario = []
    for i in range((sig - inicio_mes).days):
        f = inicio_mes + timedelta(days=i)
        cs = Cita.objects.filter(dentista=dentista, fecha=f)
        procesadas = []
        for c in cs:
            pasada = (f < hoy) or (f == hoy and c.hora_fin < hora_actual)
            procesadas.append({"paciente": c.paciente.nombre, "hora": c.hora_inicio.strftime("%H:%M"), "clase_estado": "cita-pasada" if pasada else c.estado.lower()})
        calendario.append({"dia": f, "label_dia": f.strftime("%a"), "clases": "hoy" if f == hoy else "", "citas": procesadas})

    return render(request, "dentista/dashboard.html", {
        "dentista": dentista, "citas_hoy": citas_hoy, "kpi_pacientes": kpi_pacs, "kpi_pendientes": kpi_pend,
        "ingresos_mes": ingresos, "proxima_cita": prox, "calendario_dias": calendario,
        "riesgos": [calcular_riesgo_paciente(p) for p in Paciente.objects.filter(dentista=dentista)],
        "sugerencias": optimizar_agenda(citas_hoy),
        "pagos": Pago.objects.filter(cita__dentista=dentista).order_by("-created_at")[:5]
    })

# ============================================================
# AGENDA
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
            citas_info = []
            for c in Cita.objects.filter(fecha=fecha):
                pasada = (fecha < hoy) or (fecha == hoy and c.hora_fin < hora_actual)
                citas_info.append({
                    "obj": c, "es_mia": c.dentista == dentista,
                    "clase_extra": "ghost-mode" if pasada else ""
                })
            semana.append({
                "fecha": fecha,
                "tipo_dia": "laboral" if Horario.objects.filter(dentista=dentista, dia_semana=fecha.isoweekday()).exists() else "descanso",
                "citas": citas_info
            })
        semanas.append(semana)

    return render(request, "dentista/agenda.html", {"dentista": dentista, "semanas": semanas, "fecha_actual": hoy})

# ============================================================
# API SLOTS (Para Cita Manual)
# ============================================================
@login_required
def obtener_slots_disponibles(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    fecha_str, s_id = request.GET.get('fecha'), request.GET.get('servicio_id')
    if not fecha_str or not s_id: return JsonResponse({'slots': []})

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        duracion = Servicio.objects.get(id=s_id).duracion_estimada
    except: return JsonResponse({'slots': []})

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
# API ODONTOGRAMA (CORREGIDA CON NOTAS Y DEBUG)
# ============================================================
@login_required
def odontograma_data(request, id):
    paciente = get_object_or_404(Paciente, id=id, dentista=request.user.dentista)
    dientes = Diente.objects.filter(paciente=paciente)
    data = [{"diente": d.numero, "estado": d.estado, "nota": d.nota or ""} for d in dientes]
    return JsonResponse(data, safe=False)

# EN dentista/views.py

# EN dentista/views.py (Reemplaza solo esta función)

@login_required
def odontograma_guardar(request, id):
    if request.method == "POST":
        try:
            paciente = get_object_or_404(Paciente, id=id, dentista=request.user.dentista)
            
            # Leer datos
            body = json.loads(request.body)
            print(f"DEBUG RECIBIDO: {body}") # Para confirmar

            # --- FIX DE COMPATIBILIDAD ---
            # Intentamos leer 'diente' (nuevo) O 'tooth' (viejo/caché)
            num = body.get('diente') or body.get('tooth')
            
            # Intentamos leer 'estado' (nuevo) O 'status' (viejo/caché)
            estado = body.get('estado') or body.get('status')
            
            nota = body.get('nota', '')

            # Validación
            if not num:
                print("ERROR: No se encontró el número de diente en los datos enviados.")
                return JsonResponse({'status': 'error', 'msg': 'Falta número de diente'}, status=400)

            # Normalizar nombres de estado (por si el JS viejo manda 'ortodoncia' en vez de 'bracket')
            if estado == 'ortodoncia': estado = 'bracket'
            if estado == 'restauracion': estado = 'caries'
            if estado == 'observacion': estado = 'corona'

            # Guardar en BD
            if estado == 'sano':
                Diente.objects.filter(paciente=paciente, numero=num).delete()
            else:
                Diente.objects.update_or_create(
                    paciente=paciente, 
                    numero=num,
                    defaults={'estado': estado, 'nota': nota}
                )
            
            return JsonResponse({'status': 'success'})

        except Exception as e:
            print(f"ERROR CRÍTICO: {e}")
            return JsonResponse({'status': 'error', 'msg': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)

# ============================================================
# CRUD PACIENTES & CITAS
# ============================================================
@login_required
def crear_cita_manual(request):
    dentista = get_object_or_404(Dentista, user=request.user)
    if request.method == "POST":
        p_id, s_id, f_str, h_str = request.POST.get("paciente"), request.POST.get("servicio"), request.POST.get("fecha"), request.POST.get("hora")
        if p_id and s_id and f_str and h_str:
            f = datetime.strptime(f_str, "%Y-%m-%d").date()
            h = datetime.strptime(h_str, "%H:%M").time()
            s = Servicio.objects.get(id=s_id)
            Cita.objects.create(dentista=dentista, paciente_id=p_id, servicio=s, fecha=f, hora_inicio=h, hora_fin=(datetime.combine(f, h)+timedelta(minutes=s.duracion_estimada)).time(), estado="PENDIENTE")
            messages.success(request, "Cita creada.")
            return redirect("dentista:agenda")
    return render(request, "dentista/crear_cita_manual.html", {
        "dentista": dentista, "pacientes": Paciente.objects.filter(dentista=dentista),
        "servicios": Servicio.objects.filter(dentista=dentista),
        "fecha_min": date.today().strftime("%Y-%m-%d"), "fecha_max": (date.today()+timedelta(days=60)).strftime("%Y-%m-%d")
    })

@login_required
@require_POST
def eliminar_cita(request, id):
    get_object_or_404(Cita, id=id, dentista__user=request.user).delete()
    return redirect("dentista:agenda")

@login_required
def consulta(request, id):
    cita = get_object_or_404(Cita, id=id, dentista__user=request.user)
    if request.method == "POST":
        cita.notas = request.POST.get("notas_clinicas", "")
        if request.FILES.get("archivo_adjunto"): cita.archivo_adjunto = request.FILES.get("archivo_adjunto")
        if "pagado" in request.POST:
            cita.estado = "COMPLETADA"
            Pago.objects.update_or_create(cita=cita, defaults={"monto": request.POST.get("monto", cita.servicio.precio), "estado": "COMPLETADO", "metodo": "EFECTIVO"})
        else:
            if cita.estado not in ["COMPLETADA", "CANCELADA"]: cita.estado = "CONFIRMADA"
        cita.save()
        messages.success(request, "Actualizado.")
        return redirect("dentista:consulta", id=cita.id)
    return render(request, "dentista/consulta.html", {"dentista": cita.dentista, "cita": cita, "pago": getattr(cita, 'pago_relacionado', None)})

@login_required
def pacientes(request):
    d = get_object_or_404(Dentista, user=request.user)
    qs = Paciente.objects.filter(dentista=d).order_by("nombre")
    if q := request.GET.get("q", "").strip(): qs = qs.filter(Q(nombre__icontains=q) | Q(telefono__icontains=q))
    return render(request, "dentista/pacientes.html", {"dentista": d, "pacientes": qs, "query": q})

@login_required
def registrar_paciente(request):
    d = get_object_or_404(Dentista, user=request.user)
    if request.method == "POST":
        p = Paciente(dentista=d, nombre=request.POST.get("nombre"), telefono=request.POST.get("telefono",""), direccion=request.POST.get("direccion",""), antecedentes=request.POST.get("antecedentes",""))
        if f := request.POST.get("fecha_nacimiento"): p.fecha_nacimiento = datetime.strptime(f, "%Y-%m-%d").date()
        if request.FILES.get("imagen"): p.imagen = request.FILES.get("imagen")
        p.save()
        return redirect("dentista:detalle_paciente", id=p.id)
    return render(request, "dentista/registrar_paciente.html", {"dentista": d})

@login_required
def editar_paciente(request, id):
    p = get_object_or_404(Paciente, id=id, dentista__user=request.user)
    if request.method == "POST":
        p.nombre = request.POST.get("nombre")
        p.telefono = request.POST.get("telefono")
        p.direccion = request.POST.get("direccion")
        p.antecedentes = request.POST.get("antecedentes")
        if f := request.POST.get("fecha_nacimiento"): p.fecha_nacimiento = datetime.strptime(f, "%Y-%m-%d").date()
        if request.FILES.get("imagen"): p.imagen = request.FILES.get("imagen")
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
def pagos(request):
    d = get_object_or_404(Dentista, user=request.user)
    qs = Pago.objects.filter(cita__dentista=d).order_by("-created_at")
    hoy = date.today()
    return render(request, "dentista/pagos.html", {
        "dentista": d, "pagos": qs,
        "kpi_mes": qs.filter(created_at__date__gte=hoy.replace(day=1)).aggregate(Sum("monto"))["monto__sum"] or 0,
        "kpi_efectivo": qs.filter(metodo="EFECTIVO").aggregate(Sum("monto"))["monto__sum"] or 0,
        "kpi_digital": qs.filter(metodo__in=["TARJETA", "TRANSFERENCIA"]).aggregate(Sum("monto"))["monto__sum"] or 0,
        "kpi_total": qs.aggregate(Sum("monto"))["monto__sum"] or 0
    })

# Vistas simples
@login_required
def reportes(request): return render(request, "dentista/reportes.html", {"dentista": request.user.dentista})
@login_required
def servicios(request): return render(request, "dentista/servicios.html", {"dentista": request.user.dentista, "servicios": Servicio.objects.filter(dentista=request.user.dentista)})
@login_required
def penalizaciones(request): return render(request, "dentista/penalizaciones.html", {"dentista": request.user.dentista, "pendientes": Pago.objects.filter(cita__dentista=request.user.dentista, estado="PENDIENTE")})
@login_required
def configuracion(request): return render(request, "dentista/configuracion.html", {"dentista": request.user.dentista})
@login_required
def soporte(request): return render(request, "dentista/soporte.html", {"dentista": request.user.dentista})