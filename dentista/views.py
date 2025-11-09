from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from domain.models import Cita, Paciente, Servicio, Pago, Disponibilidad
from domain.ai_services import calcular_score_riesgo

# ==============================================================================
# VISTAS PRINCIPALES (REALES)
# ==============================================================================

@login_required
def dashboard(request):
    """Centro de control principal."""
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
    """Agenda completa de citas futuras."""
    dentista = request.user.perfil_dentista
    citas_futuras = Cita.objects.filter(dentista=dentista, fecha_hora_inicio__gte=timezone.now().replace(hour=0, minute=0, second=0)).order_by('fecha_hora_inicio')
    return render(request, "dentista/agenda.html", {'citas': citas_futuras, 'total_futuras': citas_futuras.count()})

@login_required
def pacientes(request):
    """Directorio de pacientes."""
    query = request.GET.get('q', '')
    pacientes_list = Paciente.objects.all().order_by('nombre')
    if query:
        pacientes_list = pacientes_list.filter(Q(nombre__icontains=query) | Q(user__email__icontains=query) | Q(telefono__icontains=query))
    return render(request, "dentista/pacientes.html", {'pacientes': pacientes_list, 'query': query})

@login_required
def detalle_paciente(request, paciente_id):
    """Expediente digital del paciente."""
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historial = Cita.objects.filter(paciente=paciente).order_by('-fecha_hora_inicio')
    context = {'paciente': paciente, 'historial': historial, 'total_citas': historial.count(), 'citas_completadas': historial.filter(estado=Cita.EstadoCita.COMPLETADA).count()}
    return render(request, "dentista/detalle_paciente.html", context)

@login_required
def gestionar_servicios(request):
    """Panel para administrar el catálogo de tratamientos."""
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
    """Control financiero."""
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
    """Lista de inasistencias y multas."""
    if not hasattr(request.user, 'perfil_dentista'): return redirect("home")
    dentista = request.user.perfil_dentista
    lista_penalizaciones = Cita.objects.filter(dentista=dentista, estado=Cita.EstadoCita.NO_SHOW, pago_relacionado__isnull=True).order_by('-fecha_hora_inicio')
    return render(request, "dentista/penalizaciones.html", {'penalizaciones': lista_penalizaciones, 'total_deuda': lista_penalizaciones.count() * 500})

@login_required
def configuracion(request):
    """Panel para que el dentista gestione sus horarios laborales."""
    if not hasattr(request.user, 'perfil_dentista'): return redirect("home")
    dentista = request.user.perfil_dentista

    if request.method == 'POST':
        dia = request.POST.get('dia')
        inicio = request.POST.get('hora_inicio')
        fin = request.POST.get('hora_fin')
        try:
            Disponibilidad.objects.create(dentista=dentista, dia_semana=int(dia), hora_inicio=inicio, hora_fin=fin)
            messages.success(request, "Nuevo horario agregado correctamente.")
        except Exception as e:
             messages.error(request, f"Error al guardar horario: {e}")
        return redirect('dentista:configuracion')

    horarios = Disponibilidad.objects.filter(dentista=dentista).order_by('dia_semana', 'hora_inicio')
    return render(request, "dentista/configuracion.html", {'dentista': dentista, 'horarios': horarios, 'dias_semana': Disponibilidad.DIAS_SEMANA})

@login_required
def eliminar_horario(request, horario_id):
    horario = get_object_or_404(Disponibilidad, id=horario_id, dentista__user=request.user)
    horario.delete()
    messages.success(request, "Horario eliminado.")
    return redirect('dentista:configuracion')

# ==============================================================================
# ACCIONES RÁPIDAS
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

@login_required
def completar_cita(request, cita_id): return redirect('dentista:vista_consulta', cita_id=cita_id)

# ==============================================================================
# VISTAS PLACEHOLDER
# ==============================================================================

@login_required
def reportes_placeholder(request): return render(request, "dentista/base.html", {"dcontent": "<h1>Reportes (Próximamente)</h1>"})
@login_required
def soporte_placeholder(request): return render(request, "dentista/base.html", {"dcontent": "<h1>Soporte (Próximamente)</h1>"})
# Redirecciones para mantener compatibilidad si algo llama a las viejas urls
@login_required
def pagos_placeholder(request): return redirect('dentista:pagos')
@login_required
def servicios_placeholder(request): return redirect('dentista:servicios')
@login_required
def penalizaciones_placeholder(request): return redirect('dentista:penalizaciones')
@login_required
def configuracion_placeholder(request): return redirect('dentista:configuracion')