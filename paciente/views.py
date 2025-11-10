from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils.timezone import make_aware
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from datetime import datetime, timedelta
from textblob import TextBlob # Para la IA de sentimientos

# Importamos tus modelos y servicios
from domain.models import Cita, Servicio, Dentista, Pago, EncuestaSatisfaccion
from .services import obtener_horarios_disponibles
from .mp_service import crear_preferencia_pago

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
        estado__in=[Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.CONFIRMADA, Cita.EstadoCita.CONFIRMADA_PACIENTE, Cita.EstadoCita.CONFIRMADA_DENTISTA],
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
# MOTOR DE AGENDAMIENTO
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
    except Servicio.DoesNotExist:
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
        servicio = Servicio.objects.get(id=servicio_id)
        dentista = Dentista.objects.first()
        if not dentista: raise Exception("No hay dentistas registrados.")

        inicio_naive = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
        fecha_inicio = make_aware(inicio_naive)
        fecha_fin = fecha_inicio + timedelta(minutes=servicio.duracion_estimada)

        Cita.objects.create(
            paciente=paciente, dentista=dentista, servicio=servicio,
            fecha_hora_inicio=fecha_inicio, fecha_hora_fin=fecha_fin,
            estado=Cita.EstadoCita.CONFIRMADA, notas=notas
        )
        # (Aquí iría el envío de correo que ya probamos)
        messages.success(request, "¡Tu cita ha sido agendada exitosamente!")

    except Exception as e:
        messages.error(request, f"No se pudo agendar la cita: {str(e)}")

    return redirect('paciente:dashboard')

# ==============================================================================
# FLUJO DE PAGOS (MERCADOPAGO)
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
        messages.error(request, f"Error de pago: {e}")
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
                defaults={'monto': cita.servicio.precio, 'metodo': Pago.MetodoPago.MERCADOPAGO, 'estado': Pago.EstadoPago.COMPLETADO, 'mercadopago_id': collection_id}
            )
            messages.success(request, "¡Pago recibido con éxito!")
        except Cita.DoesNotExist: pass
    return redirect('paciente:dashboard')

@login_required
def pago_fallido(request):
    messages.error(request, "El proceso de pago falló. Intenta de nuevo.")
    return redirect('paciente:dashboard')

@login_required
def pago_pendiente(request):
    messages.warning(request, "Pago en proceso. Se actualizará pronto.")
    return redirect('paciente:dashboard')

# ==============================================================================
# ENCUESTA DE SATISFACCIÓN (IA)
# ==============================================================================

@login_required
def encuesta_satisfaccion(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)
    if cita.estado != Cita.EstadoCita.COMPLETADA:
        return redirect('paciente:dashboard')
    if hasattr(cita, 'encuesta'):
        messages.info(request, "Ya opinaste sobre esta cita.")
        return redirect('paciente:dashboard')

    if request.method == 'POST':
        calificacion = int(request.POST.get('calificacion'))
        comentario = request.POST.get('comentario', '').strip()

        # ANÁLISIS DE SENTIMIENTO CON IA (TextBlob)
        sentimiento = EncuestaSatisfaccion.Sentimiento.NEUTRAL
        if comentario:
            analisis = TextBlob(comentario)
            if analisis.sentiment.polarity > 0.1:
                sentimiento = EncuestaSatisfaccion.Sentimiento.POSITIVO
            elif analisis.sentiment.polarity < -0.1:
                sentimiento = EncuestaSatisfaccion.Sentimiento.NEGATIVO

        EncuestaSatisfaccion.objects.create(
            cita=cita, calificacion=calificacion, comentario=comentario, sentimiento_ia=sentimiento
        )
        messages.success(request, "¡Gracias por tu opinión!")
        return redirect('paciente:dashboard')

    return render(request, "paciente/encuesta.html", {'cita': cita})

# ==============================================================================
# VISTAS PÚBLICAS (NO REQUIEREN LOGIN)
# ==============================================================================

@require_GET
def confirmar_por_email(request, token):
    signer = TimestampSigner()
    try:
        cita_id = signer.unsign(token, max_age=172800)
        cita = get_object_or_404(Cita, id=cita_id)
        if cita.estado == Cita.EstadoCita.PENDIENTE:
            cita.estado = Cita.EstadoCita.CONFIRMADA_PACIENTE
            cita.save()
            return HttpResponse("✅ ¡Asistencia confirmada! Gracias.")
        return HttpResponse("ℹ️ Esta cita ya había sido confirmada o no está pendiente.")
    except (BadSignature, SignatureExpired):
        return HttpResponse("❌ Enlace inválido o expirado.")

# ==============================================================================
# PLACEHOLDERS
# ==============================================================================
@login_required
def citas(request): return render(request, "paciente/citas.html")
@login_required
def pagos(request): return render(request, "paciente/pagos.html")
@login_required
def reprogramar_placeholder(request, cita_id): return HttpResponse("Reprogramar próximamente")
@login_required
def cancelar_placeholder(request, cita_id): return HttpResponse("Cancelar próximamente")