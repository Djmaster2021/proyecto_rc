import csv
import weasyprint
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth 
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from domain.models import Cita, Paciente, Servicio, Pago, Disponibilidad
from domain.ai_services import calcular_score_riesgo

# ==============================================================================
# VISTAS PRINCIPALES (REALES)
# ==============================================================================

@login_required
def dashboard(request):
    if not hasattr(request.user, 'perfil_dentista'): return redirect("home")
    dentista = request.user.perfil_dentista
    hoy = timezone.now().date()
    citas_hoy = Cita.objects.filter(dentista=dentista, fecha_hora_inicio__date=hoy, estado__in=[Cita.EstadoCita.CONFIRMADA, Cita.EstadoCita.CONFIRMADA_PACIENTE, Cita.EstadoCita.PENDIENTE]).order_by('fecha_hora_inicio')
    context = {
        "dentista": dentista, "citas_hoy": citas_hoy, "fecha_actual": hoy,
        "kpi_pacientes": Paciente.objects.count(),
        "kpi_pendientes": Cita.objects.filter(dentista=dentista, estado=Cita.EstadoCita.PENDIENTE).count(),
    }
    return render(request, "dentista/dashboard.html", context)

@login_required
def agenda(request):
    dentista = request.user.perfil_dentista
    citas_futuras = Cita.objects.filter(dentista=dentista, fecha_hora_inicio__gte=timezone.now().replace(hour=0, minute=0, second=0)).order_by('fecha_hora_inicio')
    return render(request, "dentista/agenda.html", {'citas': citas_futuras, 'total_futuras': citas_futuras.count()})

@login_required
def pacientes(request):
    query = request.GET.get('q', '')
    pacientes_list = Paciente.objects.all().order_by('nombre')
    if query:
        pacientes_list = pacientes_list.filter(Q(nombre__icontains=query) | Q(user__email__icontains=query) | Q(telefono__icontains=query))
    return render(request, "dentista/pacientes.html", {'pacientes': pacientes_list, 'query': query})

@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historial = Cita.objects.filter(paciente=paciente).order_by('-fecha_hora_inicio')
    context = {'paciente': paciente, 'historial': historial, 'total_citas': historial.count(), 'citas_completadas': historial.filter(estado=Cita.EstadoCita.COMPLETADA).count()}
    return render(request, "dentista/detalle_paciente.html", context)

@login_required
def gestionar_servicios(request):
    if not hasattr(request.user, 'perfil_dentista'): return redirect("home")
    if request.method == 'POST':
        sid, nom, pre, dur, act = request.POST.get('servicio_id'), request.POST.get('nombre'), request.POST.get('precio'), request.POST.get('duracion'), request.POST.get('activo') == 'on'
        if sid:
            s = get_object_or_404(Servicio, id=sid)
            s.nombre, s.precio, s.duracion_estimada, s.activo = nom, pre, dur, act
            s.save()
            messages.success(request, f"Servicio '{nom}' actualizado.")
        else:
            Servicio.objects.create(nombre=nom, precio=pre, duracion_estimada=dur, activo=act)
            messages.success(request, f"Nuevo servicio '{nom}' creado.")
        return redirect('dentista:servicios')
    return render(request, "dentista/servicios.html", {'servicios': Servicio.objects.all().order_by('nombre')})

@login_required
def pagos(request):
    if not hasattr(request.user, 'perfil_dentista'): return redirect("home")
    pagos_list = Pago.objects.filter(estado=Pago.EstadoPago.COMPLETADO).order_by('-created_at')
    hoy = timezone.now()
    context = {
        'pagos': pagos_list,
        'total_historico': pagos_list.aggregate(Sum('monto'))['monto__sum'] or 0,
        'total_mes': pagos_list.filter(created_at__year=hoy.year, created_at__month=hoy.month).aggregate(Sum('monto'))['monto__sum'] or 0,
    }
    return render(request, "dentista/pagos.html", context)

@login_required
def penalizaciones(request):
    if not hasattr(request.user, 'perfil_dentista'): return redirect("home")
    dentista = request.user.perfil_dentista
    lista_penalizaciones = Cita.objects.filter(dentista=dentista, estado=Cita.EstadoCita.NO_SHOW, pago_relacionado__isnull=True).order_by('-fecha_hora_inicio')
    return render(request, "dentista/penalizaciones.html", {'penalizaciones': lista_penalizaciones, 'total_deuda': lista_penalizaciones.count() * 500})

@login_required
def configuracion(request):
    if not hasattr(request.user, 'perfil_dentista'): return redirect("home")
    dentista = request.user.perfil_dentista
    if request.method == 'POST':
        try:
            Disponibilidad.objects.create(dentista=dentista, dia_semana=int(request.POST.get('dia')), hora_inicio=request.POST.get('hora_inicio'), hora_fin=request.POST.get('hora_fin'))
            messages.success(request, "Horario agregado.")
        except Exception as e:
             messages.error(request, f"Error: {e}")
        return redirect('dentista:configuracion')
    horarios = Disponibilidad.objects.filter(dentista=dentista).order_by('dia_semana', 'hora_inicio')
    return render(request, "dentista/configuracion.html", {'dentista': dentista, 'horarios': horarios, 'dias_semana': Disponibilidad.DIAS_SEMANA})

@login_required
def eliminar_horario(request, horario_id):
    get_object_or_404(Disponibilidad, id=horario_id, dentista__user=request.user).delete()
    messages.success(request, "Horario eliminado.")
    return redirect('dentista:configuracion')

# ==============================================================================
# REPORTES (CSV + PDF)
# ==============================================================================

@login_required
def reportes(request):
    if not hasattr(request.user, 'perfil_dentista'): return redirect("home")
    hoy = timezone.now().date()
    inicio = request.GET.get('inicio', hoy.replace(day=1).strftime('%Y-%m-%d'))
    fin = request.GET.get('fin', hoy.strftime('%Y-%m-%d'))
    citas = Cita.objects.filter(fecha_hora_inicio__date__range=[inicio, fin])
    ingresos = Pago.objects.filter(created_at__date__range=[inicio, fin], estado=Pago.EstadoPago.COMPLETADO).aggregate(Sum('monto'))['monto__sum'] or 0
    context = {'fecha_inicio': inicio, 'fecha_fin': fin, 'total_citas': citas.count(), 'citas_atendidas': citas.filter(estado=Cita.EstadoCita.COMPLETADA).count(), 'citas_canceladas': citas.filter(estado__in=[Cita.EstadoCita.CANCELADA_PACIENTE, Cita.EstadoCita.CANCELADA_DENTISTA, Cita.EstadoCita.NO_SHOW]).count(), 'ingresos_totales': ingresos}
    return render(request, "dentista/reportes.html", context)

@login_required
def exportar_citas_csv(request):
    inicio, fin = request.GET.get('inicio'), request.GET.get('fin')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reporte_{inicio}_{fin}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Hora', 'Paciente', 'Servicio', 'Estado', 'Monto'])
    for c in Cita.objects.filter(fecha_hora_inicio__date__range=[inicio, fin]).order_by('fecha_hora_inicio'):
        monto = c.pago_relacionado.monto if hasattr(c, 'pago_relacionado') else '0.00'
        writer.writerow([c.fecha_hora_inicio.date(), c.fecha_hora_inicio.time(), c.paciente.nombre, c.servicio.nombre, c.get_estado_display(), monto])
    return response

@login_required
def exportar_citas_pdf(request):
    inicio, fin = request.GET.get('inicio'), request.GET.get('fin')
    citas = Cita.objects.filter(fecha_hora_inicio__date__range=[inicio, fin]).order_by('fecha_hora_inicio')
    total_ing = sum(c.pago_relacionado.monto for c in citas if hasattr(c, 'pago_relacionado') and c.pago_relacionado.estado == Pago.EstadoPago.COMPLETADO)
    html = render_to_string('dentista/reporte_pdf.html', {'citas': citas, 'fecha_inicio': inicio, 'fecha_fin': fin, 'total_citas': citas.count(), 'total_ingresos': total_ing, 'generado_el': timezone.now(), 'dentista': request.user.perfil_dentista})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_{inicio}_{fin}.pdf"'
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(response)
    return response

# ==============================================================================
# API GRÁFICAS (DASHBOARD)
# ==============================================================================

@login_required
def api_datos_grafica(request):
    hoy = timezone.now().date()
    seis_meses = hoy - timezone.timedelta(days=180)
    # Aquí usamos TruncMonth que ahora sí está importado correctamente arriba
    datos = Pago.objects.filter(estado=Pago.EstadoPago.COMPLETADO, created_at__gte=seis_meses).annotate(mes=TruncMonth('created_at')).values('mes').annotate(total=Sum('monto')).order_by('mes')
    return JsonResponse({"labels": [d['mes'].strftime("%B") for d in datos], "ingresos": [float(d['total']) for d in datos], "gastos": [0]*len(datos)})

# ==============================================================================
# ACCIONES RÁPIDAS & EXTRAS
# ==============================================================================

@login_required
def confirmar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, dentista__user=request.user)
    if cita.estado == Cita.EstadoCita.PENDIENTE:
        cita.estado = Cita.EstadoCita.CONFIRMADA
        cita.save()
        messages.success(request, "Cita confirmada.")
    return redirect('dentista:dashboard')

@login_required
def vista_consulta(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, dentista__user=request.user)
    if request.method == 'POST':
        cita.notas, cita.estado = request.POST.get('notas_clinicas'), Cita.EstadoCita.COMPLETADA
        cita.save()
        messages.success(request, "Consulta finalizada.")
        return redirect('dentista:dashboard')
    return render(request, "dentista/consulta.html", {'cita': cita})

@login_required
def marcar_no_show(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, dentista__user=request.user)
    if cita.fecha_hora_inicio < timezone.now():
        cita.estado = Cita.EstadoCita.NO_SHOW
        cita.save()
        calcular_score_riesgo(cita.paciente)
        messages.warning(request, f"Inasistencia registrada para {cita.paciente.nombre}.")
    else:
        messages.error(request, "No puedes marcar inasistencia en una cita futura.")
    return redirect('dentista:dashboard')

# dentista/views.py

@login_required
def soporte(request):
    """Centro de ayuda y contacto con soporte técnico."""
    if not hasattr(request.user, 'perfil_dentista'): return redirect("home")

    if request.method == 'POST':
        asunto = request.POST.get('asunto')
        mensaje = request.POST.get('mensaje')
        # Aquí podrías mandar un correo real a tu dirección de desarrollador
        # Por ahora, solo simulamos el éxito
        messages.success(request, f"Tu reporte '{asunto}' ha sido enviado a soporte técnico.")
        return redirect('dentista:soporte')

    return render(request, "dentista/soporte.html")

@login_required
def completar_cita(request, cita_id): return redirect('dentista:vista_consulta', cita_id=cita_id)
@login_required
def soporte_placeholder(request): return render(request, "dentista/base.html", {"dcontent": "<h1>Soporte (Próximamente)</h1>"})
# Redirecciones de compatibilidad
@login_required
def pagos_placeholder(request): return redirect('dentista:pagos')
@login_required
def servicios_placeholder(request): return redirect('dentista:servicios')
@login_required
def penalizaciones_placeholder(request): return redirect('dentista:penalizaciones')
@login_required
def configuracion_placeholder(request): return redirect('dentista:configuracion')
@login_required
def reportes_placeholder(request): return redirect('dentista:reportes')