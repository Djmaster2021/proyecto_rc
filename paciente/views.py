from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils.timezone import make_aware
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from .mp_service import crear_preferencia_pago 
from domain.models import Pago

# Importamos tus modelos y el servicio de cálculo de horarios
from domain.models import Cita, Servicio, Dentista
from .services import obtener_horarios_disponibles

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
        estado__in=[Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.CONFIRMADA],
        fecha_hora_inicio__gte=datetime.now()
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
    """Procesa el formulario, crea la cita CONFIRMADA y envía correo."""
    paciente = request.user.perfil_paciente
    fecha_str = request.POST.get('fecha')
    hora_str = request.POST.get('hora')
    servicio_id = request.POST.get('servicio')
    notas = request.POST.get('notas', '').strip()

    try:
        servicio = Servicio.objects.get(id=servicio_id)
        dentista = Dentista.objects.first()
        if not dentista:
             raise Exception("No hay dentistas registrados en el sistema.")

        inicio_naive = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
        fecha_inicio = make_aware(inicio_naive)
        
        from datetime import timedelta
        fecha_fin = fecha_inicio + timedelta(minutes=servicio.duracion_estimada)

        # 1. CREAR LA CITA (DIRECTAMENTE CONFIRMADA)
        nueva_cita = Cita.objects.create(
            paciente=paciente,
            dentista=dentista,
            servicio=servicio,
            fecha_hora_inicio=fecha_inicio,
            fecha_hora_fin=fecha_fin,
            estado=Cita.EstadoCita.CONFIRMADA, # <--- ¡CAMBIO CLAVE!
            notas=notas
        )

        # 2. ENVIAR CORREO ELECTRÓNICO AUTOMÁTICO
        asunto = '✅ Confirmación de Cita - Consultorio Dental RC'
        mensaje = f"""
Hola {paciente.nombre},

¡Listo! Tu cita fue registrada con éxito.

📅 Fecha: {fecha_inicio.strftime('%d/%m/%Y')}
⏰ Hora: {fecha_inicio.strftime('%H:%M')}
🦷 Tratamiento: {servicio.nombre}
👨‍⚕️ Doctor: {dentista.nombre}

Recomendación: Por favor llega 10 minutos antes de tu cita para evitar contratiempos y actualizar cualquier dato necesario.

Si necesitas reprogramar, puedes hacerlo desde tu panel en línea.

¡Nos vemos pronto!
Consultorio Dental Rodolfo Castellón
        """
        
        try:
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email], # Envía al correo del usuario logueado
                fail_silently=True,   # Si falla el correo, no rompe la página
            )
        except Exception as e:
            print(f"Error enviando correo: {e}") # Para depuración en terminal

        messages.success(request, "¡Tu cita ha sido confirmada y te enviamos un correo con los detalles!")

    except Exception as e:
        messages.error(request, f"No se pudo agendar la cita: {str(e)}")

    return redirect('paciente:dashboard')

# ==============================================================================
# VISTAS PLACEHOLDER
# ==============================================================================

@login_required
def citas(request): return render(request, "paciente/citas.html")
@login_required
def pagos(request): return render(request, "paciente/pagos.html")
@login_required
def reprogramar_placeholder(request, cita_id): return HttpResponse(f"Reprogramar cita {cita_id}")
@login_required
def cancelar_placeholder(request, cita_id): return HttpResponse(f"Cancelar cita {cita_id}")

# ==============================================================================
# FLUJO DE PAGO (MERCADOPAGO)
# ==============================================================================

@login_required
def iniciar_pago(request, cita_id):
    """Crea la preferencia en MP y redirige al paciente a pagar."""
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)
    
    # Evitar doble pago
    if hasattr(cita, 'pago_relacionado') and cita.pago_relacionado.estado == Pago.EstadoPago.COMPLETADO:
        messages.info(request, "Esta cita ya está pagada.")
        return redirect('paciente:dashboard')

    try:
        # Usamos nuestro servicio para obtener el link
        url_pago = crear_preferencia_pago(cita, request)
        return redirect(url_pago)
    except Exception as e:
        print(f"❌ ERROR MERCADOPAGO: {e}")  # <--- ¡AGREGA ESTA LÍNEA!
        messages.error(request, f"Error al conectar con MercadoPago: {e}")
        return redirect('paciente:dashboard')
@login_required

def pago_exitoso(request):
    """El usuario volvió de MP y pagó correctamente."""
    # MP nos devuelve datos en la URL (query params)
    collection_id = request.GET.get('collection_id')
    collection_status = request.GET.get('collection_status')
    external_ref = request.GET.get('external_reference') # Este es el ID de la Cita

    if external_ref and collection_status == 'approved':
        try:
            cita = Cita.objects.get(id=external_ref)
            
            # Registrar el pago en NUESTRA base de datos
            Pago.objects.update_or_create(
                cita=cita,
                defaults={
                    'monto': cita.servicio.precio,
                    'metodo': Pago.MetodoPago.MERCADOPAGO,
                    'estado': Pago.EstadoPago.COMPLETADO,
                    'mercadopago_id': collection_id
                }
            )
            messages.success(request, "¡Pago recibido con éxito! Gracias.")
        except Cita.DoesNotExist:
            messages.error(request, "Error: No se encontró la cita pagada.")

    return redirect('paciente:dashboard')

@login_required
def pago_fallido(request):
    messages.error(request, "El proceso de pago falló o fue cancelado. Intenta de nuevo.")
    return redirect('paciente:dashboard')

@login_required
def pago_pendiente(request):
    messages.warning(request, "Tu pago está en proceso. Se actualizará cuando se confirme.")
    return redirect('paciente:dashboard')