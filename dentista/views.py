from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from domain.models import Cita, Paciente

# ==============================================================================
# VISTAS PRINCIPALES (REALES)
# ==============================================================================

@login_required
def dashboard(request):
    """Centro de control principal: Resumen del día y acciones rápidas."""
    if not hasattr(request.user, 'perfil_dentista'):
        messages.error(request, "Acceso exclusivo para personal médico.")
        return redirect("home")
    
    dentista = request.user.perfil_dentista
    hoy = timezone.now().date()

    # Citas de HOY (Confirmadas o Pendientes)
    citas_hoy = Cita.objects.filter(
        dentista=dentista,
        fecha_hora_inicio__date=hoy,
        estado__in=[Cita.EstadoCita.CONFIRMADA, Cita.EstadoCita.PENDIENTE]
    ).order_by('fecha_hora_inicio')

    # Métricas rápidas
    total_pacientes = Paciente.objects.count()
    citas_pendientes = Cita.objects.filter(dentista=dentista, estado=Cita.EstadoCita.PENDIENTE).count()

    context = {
        "dentista": dentista,
        "citas_hoy": citas_hoy,
        "fecha_actual": hoy,
        "kpi_pacientes": total_pacientes,
        "kpi_pendientes": citas_pendientes,
    }
    return render(request, "dentista/dashboard.html", context)

@login_required
def agenda(request):
    """Vista de agenda completa: Muestra todas las citas futuras agrupadas."""
    dentista = request.user.perfil_dentista
    
    # Traemos TODAS las citas de hoy en adelante, ordenadas por fecha
    citas_futuras = Cita.objects.filter(
        dentista=dentista,
        fecha_hora_inicio__gte=timezone.now().replace(hour=0, minute=0, second=0)
    ).order_by('fecha_hora_inicio')
    
    return render(request, "dentista/agenda.html", {
        'citas': citas_futuras,
        'total_futuras': citas_futuras.count()
    })

@login_required
def pacientes(request):
    """Directorio de pacientes con búsqueda básica."""
    query = request.GET.get('q', '')
    pacientes_list = Paciente.objects.all().order_by('nombre')

    if query:
        # Búsqueda por nombre, email o teléfono
        pacientes_list = pacientes_list.filter(
            Q(nombre__icontains=query) |
            Q(user__email__icontains=query) |
            Q(telefono__icontains=query)
        )

    return render(request, "dentista/pacientes.html", {
        'pacientes': pacientes_list,
        'query': query
    })

@login_required
def detalle_paciente(request, paciente_id):
    """Expediente digital del paciente: perfil + historial de citas."""
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener TODAS las citas de este paciente, ordenadas de la más reciente a la más antigua
    historial_citas = Cita.objects.filter(paciente=paciente).order_by('-fecha_hora_inicio')

    context = {
        'paciente': paciente,
        'historial': historial_citas,
        'total_citas': historial_citas.count(),
        # Calculamos citas completadas para mostrar estadísticas rápidas
        'citas_completadas': historial_citas.filter(estado=Cita.EstadoCita.COMPLETADA).count()
    }
    return render(request, "dentista/detalle_paciente.html", context)

# ==============================================================================
# ACCIONES RÁPIDAS (CAMBIO DE ESTADO DE CITAS)
# ==============================================================================

@login_required
def confirmar_cita(request, cita_id):
    """Marca una cita como CONFIRMADA."""
    cita = get_object_or_404(Cita, id=cita_id, dentista__user=request.user)
    if cita.estado == Cita.EstadoCita.PENDIENTE:
        cita.estado = Cita.EstadoCita.CONFIRMADA
        cita.save()
        messages.success(request, f"Cita de {cita.paciente} confirmada.")
    return redirect('dentista:dashboard')

@login_required
def completar_cita(request, cita_id):
    """Marca una cita como COMPLETADA (asistió)."""
    cita = get_object_or_404(Cita, id=cita_id, dentista__user=request.user)
    if cita.estado == Cita.EstadoCita.CONFIRMADA:
        cita.estado = Cita.EstadoCita.COMPLETADA
        cita.save()
        messages.success(request, f"Cita de {cita.paciente} marcada como completada.")
    return redirect('dentista:dashboard')


@login_required
def vista_consulta(request, cita_id):
    """Pantalla de atención médica: permite guardar notas y completar la cita."""
    cita = get_object_or_404(Cita, id=cita_id, dentista__user=request.user)

    if request.method == 'POST':
        # Procesar el fin de la consulta
        notas_clinicas = request.POST.get('notas_clinicas')
        
        cita.notas = notas_clinicas  # Guardamos el historial
        cita.estado = Cita.EstadoCita.COMPLETADA
        cita.save()
        
        messages.success(request, f"Consulta de {cita.paciente.nombre} finalizada y registrada.")
        return redirect('dentista:dashboard')

    # Si es GET, mostramos la pantalla de consulta
    return render(request, "dentista/consulta.html", {'cita': cita})

# ==============================================================================
# VISTAS PLACEHOLDER (Para que el menú no se rompa mientras construimos)
# ==============================================================================

def pagos_placeholder(request): return render(request, "dentista/base.html", {"ptitle": "Pagos (En construcción)"})
def servicios_placeholder(request): return render(request, "dentista/base.html", {"ptitle": "Servicios (En construcción)"})
def penalizaciones_placeholder(request): return render(request, "dentista/base.html", {"ptitle": "Penalizaciones (En construcción)"})
def reportes_placeholder(request): return render(request, "dentista/base.html", {"ptitle": "Reportes (En construcción)"})
def configuracion_placeholder(request): return render(request, "dentista/base.html", {"ptitle": "Configuración (En construcción)"})
def soporte_placeholder(request): return render(request, "dentista/base.html", {"ptitle": "Soporte (En construcción)"})