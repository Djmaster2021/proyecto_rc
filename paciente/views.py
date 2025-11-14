from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils.timezone import make_aware
from django.utils import timezone
from datetime import datetime, timedelta
from textblob import TextBlob 


from domain.models import Cita, Servicio, Dentista, Pago, EncuestaSatisfaccion
from .services import obtener_horarios_disponibles
from .mp_service import crear_preferencia_pago
from .forms import PacientePerfilForm # Asegúrate de tener este archivo forms.py creado

# ==============================================================================
# VISTAS PRINCIPALES
# ==============================================================================

@login_required
def dashboard(request):
    if not hasattr(request.user, 'perfil_paciente'):
        messages.error(request, "Acceso restringido a pacientes.")
        return redirect('home')
    
    paciente = request.user.perfil_paciente
    
    proxima_cita = Cita.objects.filter(
        paciente=paciente,
        estado__in=[
            Cita.EstadoCita.PENDIENTE, 
            Cita.EstadoCita.CONFIRMADA, 
            Cita.EstadoCita.CONFIRMADA_PACIENTE, 
            Cita.EstadoCita.CONFIRMADA_DENTISTA
        ],
        fecha_hora_inicio__gte=timezone.now()
    ).order_by('fecha_hora_inicio').first()

    historial = Cita.objects.filter(paciente=paciente).order_by('-fecha_hora_inicio')
    servicios = Servicio.objects.filter(activo=True)

    context = {
        'paciente': paciente,
        'proxima_cita': proxima_cita,
        'historial': historial,
        'servicios': servicios,
    }
    return render(request, "paciente/dashboard.html", context)

# ==============================================================================
# MOTOR DE AGENDAMIENTO (API + LÓGICA)
# ==============================================================================

@login_required
def api_horarios_disponibles(request):
    fecha_str = request.GET.get('fecha')
    servicio_id = request.GET.get('servicio_id')

    if not fecha_str or not servicio_id:
        return JsonResponse([], safe=False)

    try:
        servicio = Servicio.objects.get(id=servicio_id)
        horarios = obtener_horarios_disponibles(fecha_str, servicio.duracion_estimada)
        return JsonResponse(horarios, safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)

@login_required
@require_POST
def agendar_cita(request):
    paciente = request.user.perfil_paciente
    fecha_str = request.POST.get('fecha')
    hora_str = request.POST.get('hora')
    servicio_id = request.POST.get('servicio')
    notas = request.POST.get('notas', '').strip()

    try:
        if not fecha_str or not hora_str or not servicio_id:
             raise Exception("Faltan datos obligatorios.")

        # --- VALIDACIÓN DE FECHAS ---
        fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hoy = timezone.now().date()
        limite = hoy + timedelta(days=30)

        if fecha_seleccionada < hoy:
            raise Exception("No se puede agendar en fechas pasadas.")
        
        if fecha_seleccionada > limite:
            raise Exception("Solo se permite agendar con máximo 30 días de anticipación.")
        
        if fecha_seleccionada.weekday() == 6: 
            raise Exception("Los domingos no son días laborales.")
        # --------------------------------------

        servicio = Servicio.objects.get(id=servicio_id)
        dentista = Dentista.objects.first() 
        if not dentista: raise Exception("No hay dentistas disponibles.")

        inicio_naive = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
        fecha_inicio = make_aware(inicio_naive)
        fecha_fin = fecha_inicio + timedelta(minutes=servicio.duracion_estimada)

        colision = Cita.objects.filter(
            dentista=dentista,
            fecha_hora_inicio__lt=fecha_fin,
            fecha_hora_fin__gt=fecha_inicio,
            estado__in=[Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.CONFIRMADA]
        ).exists()

        if colision:
            raise Exception("Ese horario ya está ocupado.")

        Cita.objects.create(
            paciente=paciente, dentista=dentista, servicio=servicio,
            fecha_hora_inicio=fecha_inicio, fecha_hora_fin=fecha_fin,
            estado=Cita.EstadoCita.CONFIRMADA, notas=notas
        )
        
        messages.success(request, "¡Cita agendada exitosamente!")

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")

    return redirect('paciente:dashboard')

# ==============================================================================
# ACCIONES: CANCELAR Y REPROGRAMAR (REGLAS ESTRICTAS)
# ==============================================================================

@login_required
@require_POST
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)
    
    # REGLA: 24 HORAS DE ANTICIPACIÓN
    tiempo_restante = cita.fecha_hora_inicio - timezone.now()
    if tiempo_restante < timedelta(hours=24):
        messages.error(request, "⚠️ No puedes cancelar. Debes hacerlo con 24 horas de anticipación.")
        return redirect('paciente:dashboard')

    cita.estado = Cita.EstadoCita.CANCELADA_PACIENTE
    cita.save()
    messages.success(request, "Cita cancelada. Para agendar nuevamente deberás crear una nueva solicitud.")
    return redirect('paciente:dashboard')

@login_required
@require_POST
def reprogramar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)
    
    # REGLA 1: LÍMITE DE 1 VEZ
    if cita.veces_reprogramada >= 1:
        messages.error(request, "⚠️ Límite alcanzado. Solo se permite 1 reprogramación por cita. Contacta al consultorio.")
        return redirect('paciente:dashboard')

    # REGLA 2: 24 HORAS DE ANTICIPACIÓN
    if (cita.fecha_hora_inicio - timezone.now()) < timedelta(hours=24):
        messages.error(request, "⚠️ Demasiado tarde. Se requieren 24 horas de antelación para reprogramar.")
        return redirect('paciente:dashboard')
    
    fecha_str = request.POST.get('fecha')
    hora_str = request.POST.get('hora')
    
    try:
        fecha_sel = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        if fecha_sel > timezone.now().date() + timedelta(days=30):
            raise Exception("Máximo 30 días de anticipación.")
        if fecha_sel.weekday() == 6:
            raise Exception("Domingo no laborable.")

        inicio_naive = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
        fecha_inicio = make_aware(inicio_naive)
        fecha_fin = fecha_inicio + timedelta(minutes=cita.servicio.duracion_estimada)

        colision = Cita.objects.filter(
            dentista=cita.dentista,
            fecha_hora_inicio__lt=fecha_fin,
            fecha_hora_fin__gt=fecha_inicio,
            estado__in=[Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.CONFIRMADA]
        ).exclude(id=cita.id).exists()

        if colision:
            raise Exception("Horario ocupado.")

        cita.fecha_hora_inicio = fecha_inicio
        cita.fecha_hora_fin = fecha_fin
        cita.estado = Cita.EstadoCita.CONFIRMADA
        # AUMENTAR CONTADOR
        cita.veces_reprogramada += 1
        cita.save()
        
        messages.success(request, f"Cita reprogramada con éxito. (Te quedan 0 cambios disponibles)")

    except Exception as e:
        messages.error(request, f"No se pudo reprogramar: {e}")

    return redirect('paciente:dashboard')

# ==============================================================================
# EDICIÓN DE PERFIL
# ==============================================================================

@login_required
@require_POST
def editar_perfil(request):
    paciente = request.user.perfil_paciente
    form = PacientePerfilForm(request.POST, request.FILES, instance=paciente, user=request.user)
    
    if form.is_valid():
        form.save()
        messages.success(request, "¡Perfil actualizado correctamente!")
    else:
        messages.error(request, "Error al actualizar. Revisa los datos.")
    
    return redirect('paciente:dashboard')

# ==============================================================================
# PAGOS Y ENCUESTAS
# ==============================================================================

@login_required
def iniciar_pago(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)
    if hasattr(cita, 'pago_relacionado') and cita.pago_relacionado.estado == Pago.EstadoPago.COMPLETADO:
        return redirect('paciente:dashboard')
    try:
        url_pago = crear_preferencia_pago(cita, request)
        return redirect(url_pago)
    except Exception as e:
        messages.error(request, f"Error iniciando pago: {e}")
        return redirect('paciente:dashboard')

@login_required
def pago_exitoso(request):
    collection_id = request.GET.get('collection_id')
    collection_status = request.GET.get('collection_status')
    external_ref = request.GET.get('external_reference')

    if external_ref and collection_status == 'approved':
        try:
            cita = Cita.objects.get(id=external_ref)
            Pago.objects.update_or_create(
                cita=cita,
                defaults={
                    'monto': cita.servicio.precio, 
                    'metodo': Pago.MetodoPago.MERCADOPAGO, 
                    'estado': Pago.EstadoPago.COMPLETADO, 
                    'mercadopago_id': collection_id
                }
            )
            messages.success(request, "¡Pago recibido con éxito!")
        except Cita.DoesNotExist: pass
    return redirect('paciente:dashboard')

@login_required
def pago_fallido(request):
    messages.error(request, "Pago fallido o cancelado.")
    return redirect('paciente:dashboard')

@login_required
def pago_pendiente(request):
    messages.warning(request, "Pago pendiente.")
    return redirect('paciente:dashboard')

@login_required
def encuesta_satisfaccion(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)

    # Solo citas completadas
    if cita.estado != 'COMPLETADA':
        return redirect('paciente:dashboard')

    # Traer encuesta existente si la hay
    encuesta = getattr(cita, "encuesta", None)

    if request.method == "POST":
        calificacion = int(request.POST.get("calificacion", 0))
        comentario = request.POST.get("comentario", "").strip()

        if encuesta is None:
            encuesta = EncuestaSatisfaccion.objects.create(
                cita=cita,
                calificacion=calificacion,
                comentario=comentario
            )
        else:
            encuesta.calificacion = calificacion
            encuesta.comentario = comentario
            encuesta.save()

        # Aquí ya puede verlo el dentista leyendo cita.encuesta
        return redirect('paciente:dashboard')

    return render(request, "paciente/encuestas.html", {
        "cita": cita,
        "encuesta": encuesta,
    })
@require_GET
def confirmar_por_email(request, token):
    return HttpResponse("Confirmación recibida.")

# Placeholders
@login_required
def citas(request): return render(request, "paciente/citas.html")
@login_required
def pagos(request): return render(request, "paciente/pagos.html")