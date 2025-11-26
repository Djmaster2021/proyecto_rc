from datetime import datetime, timedelta
import mercadopago
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.conf import settings

from domain.models import (
    Cita, Paciente, Servicio, Dentista, Pago, EncuestaSatisfaccion,
)
from domain.notifications import enviar_correo_confirmacion_cita
from domain.ai_services import calcular_penalizacion_paciente

from .forms import PacientePerfilForm
from .services import obtener_horarios_disponibles


# ==============================================================================
# DASHBOARD PACIENTE
# ==============================================================================

@login_required
def dashboard(request):
    """
    Panel principal del paciente:
    - Próxima cita.
    - Historial.
    - Servicios disponibles.
    """
    if not hasattr(request.user, "perfil_paciente"):
        return redirect("home")

    paciente = request.user.perfil_paciente
    hoy = timezone.localdate()

    estados_proximas = [
        Cita.EstadoCita.PENDIENTE,
        Cita.EstadoCita.CONFIRMADA,
    ]

    # Próximas citas (a partir de ahora)
    citas_futuras_qs = (
        Cita.objects.filter(
            paciente=paciente,
            fecha_hora_inicio__gte=timezone.now(),
            estado__in=estados_proximas,
        )
        .order_by("fecha_hora_inicio")
    )
    proxima_cita = citas_futuras_qs.first()

    # Historial (las demás)
    citas_historial = (
        Cita.objects.filter(paciente=paciente)
        .exclude(id__in=citas_futuras_qs.values("id"))
        .order_by("-fecha_hora_inicio")
    )

    servicios = Servicio.objects.filter(activo=True).order_by("nombre")

    context = {
        "paciente": paciente,
        "hoy": hoy,
        "proxima_cita": proxima_cita,
        "citas_historial": citas_historial,
        "servicios": servicios,
    }
    return render(request, "paciente/dashboard.html", context)


# ==============================================================================
# HORARIOS DISPONIBLES (API)
# ==============================================================================

@login_required
def api_horarios_disponibles(request):
    """
    Devuelve horarios disponibles para una fecha y servicio (JSON).
    """
    fecha_str = request.GET.get("fecha")
    servicio_id = request.GET.get("servicio_id")

    if not fecha_str or not servicio_id:
        return JsonResponse([], safe=False)

    try:
        servicio = Servicio.objects.get(id=servicio_id)
    except Servicio.DoesNotExist:
        return JsonResponse([], safe=False)

    try:
        horarios = obtener_horarios_disponibles(fecha_str, servicio.duracion_estimada)
    except Exception:
        horarios = []

    return JsonResponse(horarios, safe=False)


# ==============================================================================
# AGENDAR CITA
# ==============================================================================

@login_required
@require_POST
def agendar_cita(request):
    if not hasattr(request.user, "perfil_paciente"):
        return redirect("home")

    paciente = request.user.perfil_paciente

    # --- NUEVA REGLA: SOLO 1 CITA ACTIVA ---
    # Buscamos si ya tiene alguna cita futura que esté Pendiente o Confirmada
    cita_activa = Cita.objects.filter(
        paciente=paciente,
        estado__in=[Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.CONFIRMADA],
        fecha_hora_inicio__gte=timezone.now()
    ).exists()

    if cita_activa:
        messages.error(request, "⚠️ Ya tienes una cita programada. No puedes tener dos citas activas al mismo tiempo.")
        return redirect("paciente:dashboard")
    # ---------------------------------------

    servicio_id = request.POST.get("servicio") or request.POST.get("servicio_id")
    fecha_str = request.POST.get("fecha")
    hora_str = request.POST.get("hora") or request.POST.get("horario")

    if not (servicio_id and fecha_str and hora_str):
        messages.error(request, "Faltan datos para agendar.")
        return redirect("paciente:dashboard")

    try:
        servicio = Servicio.objects.get(id=servicio_id)
    except Servicio.DoesNotExist:
        messages.error(request, "Servicio no válido.")
        return redirect("paciente:dashboard")

    # 1. Construir fechas y horas
    try:
        fecha_sel = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hora_obj = datetime.strptime(hora_str, "%H:%M").time()
        
        # Construir objetos Aware (con zona horaria)
        inicio_naive = datetime.combine(fecha_sel, hora_obj)
        inicio = make_aware(inicio_naive, timezone=timezone.get_current_timezone())
        
        # CALCULAR FIN
        duracion_minutos = int(servicio.duracion_estimada or 60)
        fin = inicio + timedelta(minutes=duracion_minutos)
        
    except ValueError:
        messages.error(request, "Error en el formato de fecha/hora.")
        return redirect("paciente:dashboard")

    # 2. Validaciones básicas
    hoy = timezone.now().date()
    if fecha_sel < hoy:
        messages.error(request, "No puedes agendar en el pasado.")
        return redirect("paciente:dashboard")
    
    if fecha_sel.weekday() == 6: # Domingo
        messages.error(request, "Domingos no laborales.")
        return redirect("paciente:dashboard")

    # 3. Asignar Dentista
    dentista = Dentista.objects.first()
    if not dentista:
        messages.error(request, "No hay dentistas disponibles.")
        return redirect("paciente:dashboard")

    # 4. Validación de Colisión
    colisiones = Cita.objects.filter(
        dentista=dentista,
        estado__in=[Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.CONFIRMADA],
        fecha_hora_inicio__lt=fin,
        fecha_hora_fin__gt=inicio
    )

    if colisiones.exists():
        cita_choque = colisiones.first()
        hora_ocupada = cita_choque.fecha_hora_inicio.strftime('%I:%M %p')
        messages.error(request, f"⚠️ Horario ocupado cerca de las {hora_ocupada}.")
        return redirect("paciente:dashboard")

    # 5. Crear la cita
    try:
        cita = Cita.objects.create(
            paciente=paciente,
            dentista=dentista,
            servicio=servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=fin,
            estado=Cita.EstadoCita.PENDIENTE,
        )

        try:
            enviar_correo_confirmacion_cita(cita)
        except:
            pass

        messages.success(request, "¡Listo! Cita agendada correctamente.")

    except Exception as e:
        messages.error(request, f"Error interno al guardar: {e}")

    return redirect("paciente:dashboard")

    
# ==============================================================================
# CANCELAR CITA
# ==============================================================================

@login_required
@require_POST
def cancelar_cita(request, cita_id):
    """
    El paciente cancela su cita.
    Reglas:
    1. Al menos 24h de anticipación.
    2. Máximo 1 cancelación permitida en su historial.
    """
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)
    paciente = request.user.perfil_paciente

    # --- 1. NUEVA VALIDACIÓN: Límite de cancelaciones ---
    # Contamos cuántas citas tiene este paciente con estado 'CANCELADA'
    conteo_canceladas = Cita.objects.filter(
        paciente=paciente,
        estado=Cita.EstadoCita.CANCELADA
    ).count()

    if conteo_canceladas >= 1:
        messages.error(
            request, 
            "⚠️ Ya has utilizado tu única cancelación permitida. Para realizar cambios, contacta al consultorio."
        )
        return redirect("paciente:dashboard")
    # ----------------------------------------------------

    # 2. Validación de tiempo (24 horas antes)
    tiempo_restante = cita.fecha_hora_inicio - timezone.now()
    if tiempo_restante < timedelta(hours=24):
        messages.error(
            request,
            "No puedes cancelar con menos de 24 horas de anticipación. "
            "Comunícate directamente con el consultorio.",
        )
        return redirect("paciente:dashboard")

    # 3. Ejecutar la cancelación
    cita.estado = Cita.EstadoCita.CANCELADA
    cita.save()
    
    messages.success(request, "Tu cita ha sido cancelada correctamente.")
    return redirect("paciente:dashboard")

# ==============================================================================
# REPROGRAMAR CITA
# ==============================================================================

@login_required
@require_POST
def reprogramar_cita(request, cita_id):
    """
    Reprogramar cita (si la lógica de negocio lo permite).
    """
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)

    # 1. Límite de reprogramaciones
    if cita.veces_reprogramada >= 1:
        messages.error(request, "Ya utilizaste tu reprogramación permitida.")
        return redirect("paciente:dashboard")

    # 2. Tiempo de anticipación (24h)
    tiempo_restante = cita.fecha_hora_inicio - timezone.now()
    if tiempo_restante < timedelta(hours=24):
        messages.error(request, "No puedes reprogramar con menos de 24h.")
        return redirect("paciente:dashboard")

    fecha_str = request.POST.get("fecha")
    hora_str = request.POST.get("hora")

    if not (fecha_str and hora_str):
        messages.error(request, "Selecciona nueva fecha y hora.")
        return redirect("paciente:dashboard")

    try:
        nueva_fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        nueva_hora = datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        messages.error(request, "Formato de fecha inválido.")
        return redirect("paciente:dashboard")

    inicio_naive = datetime.combine(nueva_fecha, nueva_hora)
    inicio = make_aware(inicio_naive, timezone=timezone.get_current_timezone())
    duracion = int(cita.servicio.duracion_estimada or 30)
    fin = inicio + timedelta(minutes=duracion)

    # 3. Colisión
    hay_colision = (
        Cita.objects.filter(
            dentista=cita.dentista,
            fecha_hora_inicio__lt=fin,
            fecha_hora_fin__gt=inicio,
            estado__in=[Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.CONFIRMADA],
        )
        .exclude(id=cita.id)
        .exists()
    )

    if hay_colision:
        messages.error(request, "El nuevo horario está ocupado.")
        return redirect("paciente:dashboard")

    # 4. Actualizar
    cita.fecha_hora_inicio = inicio
    cita.fecha_hora_fin = fin
    cita.estado = Cita.EstadoCita.CONFIRMADA
    cita.veces_reprogramada += 1
    cita.save()

    messages.success(request, "Cita reprogramada correctamente.")
    return redirect("paciente:dashboard")


# ==============================================================================
# CONFIRMACIÓN (PLACEHOLDER)
# ==============================================================================

@login_required
def confirmar_por_email(request, token):
    messages.info(request, "Enlace recibido. (Funcionalidad placeholder)")
    return redirect("paciente:dashboard")


# ==============================================================================
# PERFIL DEL PACIENTE
# ==============================================================================

@login_required
@require_POST
def editar_perfil(request):
    if not hasattr(request.user, "perfil_paciente"):
        return redirect("home")

    paciente = request.user.perfil_paciente
    form = PacientePerfilForm(
        request.POST,
        request.FILES,
        instance=paciente,
        user=request.user,
    )

    if form.is_valid():
        form.save()
        messages.success(request, "Perfil actualizado.")
    else:
        messages.error(request, "Error al actualizar datos.")

    return redirect("paciente:dashboard")


# ==============================================================================
# PAGOS (MERCADOPAGO)
# ==============================================================================

@login_required
def iniciar_pago(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)

    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        messages.error(request, "Error: Falta Token MP.")
        return redirect("paciente:dashboard")

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    # Preferencia de pago
    preference_data = {
        "items": [
            {
                "title": f"Cita: {cita.servicio.nombre}",
                "quantity": 1,
                "unit_price": float(cita.servicio.precio),
                "currency_id": "MXN"
            }
        ],
        "payer": {
            "email": "test_user_123456@test.com" # Email falso forzado para Sandbox
        },
        "back_urls": {
            "success": request.build_absolute_uri(reverse("paciente:pago_exitoso")),
            "failure": request.build_absolute_uri(reverse("paciente:pago_fallido")),
            "pending": request.build_absolute_uri(reverse("paciente:pago_pendiente")),
        },
        # "auto_return": "approved", # Comentado para evitar error de validación
        "external_reference": str(cita.id)
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        if "init_point" in preference:
            # Usamos sandbox_init_point para pruebas
            return redirect(preference["sandbox_init_point"])
        else:
            print("\n🔴 ERROR MP:", preference)
            messages.error(request, "Error al generar pago.")

    except Exception as e:
        print(f"🔴 EXCEPCIÓN: {e}")
        messages.error(request, "Error de conexión con MercadoPago.")

    return redirect("paciente:dashboard")


@login_required
def pago_exitoso(request):
    collection_status = request.GET.get("collection_status")
    external_ref = request.GET.get("external_reference")
    payment_id = request.GET.get("payment_id")

    if collection_status == "approved" and external_ref:
        try:
            cita = Cita.objects.get(id=external_ref)
            Pago.objects.update_or_create(
                cita=cita,
                defaults={
                    "monto": cita.servicio.precio,
                    "metodo": Pago.MetodoPago.MERCADOPAGO,
                    "estado": Pago.EstadoPago.COMPLETADO,
                    "mercadopago_id": payment_id,
                },
            )
            messages.success(request, "¡Pago recibido con éxito!")
        except Cita.DoesNotExist:
            messages.error(request, "No se encontró la cita asociada.")
    else:
        messages.warning(request, "El pago no se completó o no fue aprobado.")

    return redirect("paciente:dashboard")


@login_required
def pago_fallido(request):
    messages.error(request, "Pago fallido o cancelado.")
    return redirect("paciente:dashboard")


@login_required
def pago_pendiente(request):
    messages.warning(request, "Tu pago está en proceso.")
    return redirect("paciente:dashboard")


# ==============================================================================
# OTRAS VISTAS
# ==============================================================================

@login_required
def pagar_penalizacion(request):
    perfil_paciente = getattr(request.user, "perfil_paciente", None)
    if perfil_paciente is None:
        return redirect("home")

    info = calcular_penalizacion_paciente(perfil_paciente)

    if info["estado"] != "pending":
        messages.info(request, "No tienes penalizaciones pendientes.")
        return redirect("paciente:dashboard")

    context = {
        "paciente": perfil_paciente,
        "penalizacion": info,
    }
    return render(request, "paciente/pagar_penalizacion.html", context)


@login_required
def encuesta_satisfaccion(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)

    if cita.estado != Cita.EstadoCita.COMPLETADA:
        return redirect("paciente:dashboard")

    encuesta = getattr(cita, "encuesta", None)

    if request.method == "POST":
        calificacion = int(request.POST.get("calificacion", 0))
        comentario = request.POST.get("comentario", "").strip()

        if encuesta is None:
            encuesta = EncuestaSatisfaccion.objects.create(
                cita=cita,
                calificacion=calificacion,
                comentario=comentario,
            )
        else:
            encuesta.calificacion = calificacion
            encuesta.comentario = comentario
            encuesta.save()

        messages.success(request, "Gracias por tu opinión.")
        return redirect("paciente:dashboard")

    return render(request, "paciente/encuestas.html", {"cita": cita, "encuesta": encuesta})