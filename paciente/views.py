from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import mercadopago
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from urllib.parse import urlencode
from django.urls import reverse
from django.db.models import Q
from django.core.cache import cache

# Importamos modelos
from domain.models import Paciente, Dentista, Cita, Pago, Servicio, Horario, PenalizacionLog, EncuestaSatisfaccion
from domain.notifications import enviar_correo_confirmacion_cita
from domain.ai_services import calcular_penalizacion_paciente, obtener_slots_disponibles
from .mp_service import crear_preferencia_pago

# Servicios auxiliares con fallback
try:
    from .services import obtener_horarios_disponibles, crear_aviso_por_cita
except ImportError:
    def obtener_horarios_disponibles(*args): return []
    def crear_aviso_por_cita(*args): pass


def _reactivar_paciente_si_penalizacion(pago):
    """
    Si el pago corresponde a una penalización (cita INASISTENCIA o monto >= $300),
    reactiva la cuenta del paciente y deja un log.
    """
    cita = getattr(pago, "cita", None)
    paciente = getattr(cita, "paciente", None)
    user = getattr(paciente, "user", None)

    if not cita or not paciente:
        return

    if cita.estado != "INASISTENCIA":
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
                motivo="Cuenta reactivada tras pago de penalización.",
                monto=pago.monto,
            )
    except Exception as exc:
        print(f"[WARN] No se pudo registrar reactivación: {exc}")

# ========================================================
# 1. COMPLETAR PERFIL
# ========================================================
@login_required
def completar_perfil_paciente(request):
    user = request.user
    if hasattr(user, 'dentista'): return redirect('dentista:dashboard')
    if hasattr(user, 'paciente_perfil'): return redirect('paciente:dashboard')

    dentista_asignado = Dentista.objects.first()
    if not dentista_asignado:
        messages.error(
            request,
            "No hay un dentista configurado aún. Contacta al administrador para registrar uno antes de continuar.",
        )
        return redirect('home')

    # Si llega aquí sin perfil de paciente, lo creamos automáticamente con los datos del usuario
    nombre = f"{user.first_name} {user.last_name}".strip() or (user.email.split("@")[0] if user.email else user.username)
    telefono_registro = getattr(user, "telefono", "") or ""
    paciente = Paciente.objects.create(
        user=user,
        dentista=dentista_asignado,
        nombre=nombre,
        telefono=telefono_registro,
    )
    messages.info(request, "Perfil creado automáticamente. Completa tus datos desde tu perfil si lo necesitas.")
    return redirect('paciente:dashboard')


# ========================================================
# 2. DASHBOARD
# ========================================================
@login_required
def dashboard(request):
    try:
        paciente = request.user.paciente_perfil
    except:
        return redirect('paciente:completar_perfil')

    # Aseguramos que el paciente tenga dentista asignado (fallback al primero)
    if not paciente.dentista:
        from domain.models import Dentista
        dentista_default = Dentista.objects.first()
        if dentista_default:
            paciente.dentista = dentista_default
            paciente.save(update_fields=["dentista"])

    hoy = timezone.localdate()
    now_local = timezone.localtime()
    current_time = now_local.time()
    penal_info = calcular_penalizacion_paciente(paciente)
    
    proxima_cita = Cita.objects.filter(
        paciente=paciente,
        estado__in=['PENDIENTE', 'CONFIRMADA']
    ).filter(
        Q(fecha__gt=hoy) | Q(fecha=hoy, hora_inicio__gte=current_time)
    ).order_by('fecha', 'hora_inicio').first()
    cancel_used_month = Cita.objects.filter(
        paciente=paciente,
        estado="CANCELADA",
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).exists()
    reprogram_used_month = Cita.objects.filter(
        paciente=paciente,
        veces_reprogramada__gte=1,
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).exists()

    historial = Cita.objects.filter(
        paciente=paciente
    ).filter(
        Q(fecha__lt=hoy) | Q(fecha=hoy, hora_inicio__lt=current_time)
    ).order_by('-fecha', '-hora_inicio').prefetch_related('encuestasatisfaccion_set')[:5]

    # --- NUEVO: Cargamos los servicios para el Modal ---
    servicios = Servicio.objects.filter(activo=True).order_by('nombre')

    pagos_pendientes = Pago.objects.filter(
        cita__paciente=paciente,
        estado="PENDIENTE"
    ).select_related("cita", "cita__servicio").order_by("-created_at")[:3]

    advertencia_manual = (
        PenalizacionLog.objects.filter(paciente=paciente, accion="ADVERTENCIA")
        .order_by("-created_at")
        .first()
    )

    context = {
        'paciente': paciente,
        'proxima_cita': proxima_cita,
        'historial': historial,
        'servicios': servicios, # <--- Agregamos esto al contexto
        'pagos_pendientes': pagos_pendientes,
        'deuda_pendiente': pagos_pendientes.exists(),
        'penal_info': penal_info,
        'cancel_used_month': cancel_used_month,
        'reprogram_used_month': reprogram_used_month,
        'advertencia_manual': advertencia_manual,
    }
    return render(request, 'paciente/dashboard.html', context)

# ========================================================
# 3. EDITAR PERFIL
# ========================================================
@login_required
def editar_perfil(request):
    try:
        paciente = request.user.paciente_perfil
    except:
        return redirect('paciente:completar_perfil')

    if request.method == 'POST':
        paciente.nombre = request.POST.get('nombre')
        paciente.direccion = request.POST.get('direccion')
        fecha = request.POST.get('fecha_nacimiento')
        if fecha: paciente.fecha_nacimiento = fecha
        paciente.save()
        messages.success(request, "Datos actualizados.")
        return redirect('paciente:dashboard')

    return render(request, 'paciente/completar_perfil.html', {
        'nombre_google': paciente.nombre,
        'telefono_actual': paciente.telefono,
        'paciente': paciente,
        'es_edicion': True
    })


# ========================================================
# 4. AGENDAR CITA (Lógica Híbrida Inteligente)
# ========================================================
@login_required
def agendar_cita(request):
    try:
        paciente = request.user.paciente_perfil
    except:
        return redirect('paciente:completar_perfil')

    penal_info = calcular_penalizacion_paciente(paciente)
    if penal_info.get("estado") in ["pending", "disabled"]:
        messages.error(request, "No puedes agendar citas hasta cubrir la penalización pendiente ($300).")
        return redirect("paciente:dashboard")

    if request.method == 'POST':
        servicio_id = request.POST.get('servicio')
        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora') 

        if servicio_id and fecha_str and hora_str:
            # 1. Obtenemos el servicio seleccionado
            servicio = get_object_or_404(Servicio, id=servicio_id)
            
            # 2. LÓGICA HÍBRIDA:
            # La cita se asigna al dentista QUE REALIZA el servicio,
            # no necesariamente al dentista de cabecera del paciente.
            dentista_especialista = servicio.dentista

            try:
                hora_inicio = datetime.strptime(hora_str, "%H:%M").time()
                fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()

                # Validación de rango de fecha (no antes de hoy, no más de 60 días y sin domingos)
                hoy = timezone.localdate()
                limite = hoy + timedelta(days=60)
                if fecha_obj < hoy:
                    messages.error(request, "No puedes agendar en fechas pasadas.")
                    return redirect('paciente:dashboard')
                if fecha_obj > limite:
                    messages.error(request, "Solo puedes agendar hasta 60 días a partir de hoy.")
                    return redirect('paciente:dashboard')
                if fecha_obj.weekday() == 6:  # domingo
                    messages.error(request, "No se atiende los domingos. Elige otro día.")
                    return redirect('paciente:dashboard')

                inicio_dt = datetime.combine(fecha_obj, hora_inicio)
                fin_dt = inicio_dt + timedelta(minutes=servicio.duracion_estimada or 30)

                # Evita agendar en horas ya pasadas el mismo día
                now_local = timezone.localtime()
                if fecha_obj == now_local.date() and hora_inicio <= now_local.time():
                    messages.error(request, "No puedes agendar en una hora que ya pasó.")
                    return redirect('paciente:dashboard')

                # Validar que el horario esté disponible para ese servicio/dentista
                slots_libres = set(
                    obtener_slots_disponibles(
                        dentista_especialista,
                        fecha_obj,
                        servicio,
                        minutos_bloque=15,
                    )
                )
                slot_key = hora_inicio.strftime("%H:%M")
                if slot_key not in slots_libres:
                    messages.error(request, "Ese horario ya no está disponible. Elige otro.")
                    return redirect('paciente:dashboard')
                
                # Creamos la cita con el especialista correcto
                nueva_cita = Cita.objects.create(
                    dentista=dentista_especialista, # <--- AQUÍ ESTÁ EL CAMBIO
                    paciente=paciente,
                    servicio=servicio,
                    fecha=fecha_obj,
                    hora_inicio=hora_inicio,
                    hora_fin=fin_dt.time(),
                    estado='PENDIENTE'
                )

                # Crear pago pendiente para mostrar en "Pagos en línea"
                try:
                    Pago.objects.get_or_create(
                        cita=nueva_cita,
                        defaults={
                            "monto": servicio.precio,
                            "metodo": "MERCADOPAGO",
                            "estado": "PENDIENTE",
                        }
                    )
                except Exception as e:
                    print(f"[WARN] No se pudo crear pago pendiente: {e}")

                # Correo de confirmación al paciente
                try:
                    enviar_correo_confirmacion_cita(nueva_cita)
                except Exception as e:
                    print(f"[WARN] No se pudo enviar correo de confirmación al paciente: {e}")
                
                crear_aviso_por_cita(
                    nueva_cita,
                    "NUEVA_CITA",
                    f"Cita solicitada por el paciente: {servicio.nombre}",
                )
                
                # Mensaje personalizado
                if dentista_especialista != paciente.dentista:
                    msg = f"Cita agendada con el especialista Dr. {dentista_especialista.nombre}."
                else:
                    msg = "Cita agendada con tu dentista correctamente."
                
                messages.success(request, msg)
                return redirect('paciente:dashboard')

            except ValueError:
                messages.error(request, "Error en los datos seleccionados.")

    # GET: Mostrar TODOS los servicios activos de la clínica
    # Ordenamos primero por el dentista del paciente (para sugerirlos primero) y luego por nombre
    servicios = Servicio.objects.filter(activo=True).order_by('dentista__id', 'nombre')
    
    return render(request, 'paciente/agendar_cita.html', {
        'servicios': servicios,
        'dentista_cabecera': paciente.dentista
    })


# ========================================================
# 5. PAGOS & EXTRAS
# ========================================================
@login_required
def mis_pagos(request):
    try:
        paciente = request.user.paciente_perfil
    except:
        return redirect('paciente:completar_perfil')

    # Evita repetir banners de pago_ok tras cambiar idioma o recargar
    if request.GET.get("pago_ok"):
        messages.success(request, "Pago registrado correctamente.")
        return redirect("paciente:mis_pagos")

    penal_info = calcular_penalizacion_paciente(paciente)

    # Aseguramos que exista un pago pendiente para la penalización si el estado es pending
    penal_pago = (
        Pago.objects.filter(
            cita__paciente=paciente,
            estado="PENDIENTE",
            cita__estado="INASISTENCIA",
            monto__gte=Decimal("300"),
        )
        .order_by("-created_at")
        .first()
    )
    if penal_info.get("estado") == "pending" and not penal_pago:
        cita = (
            Cita.objects.filter(paciente=paciente)
            .order_by("-fecha", "-hora_inicio")
            .first()
        )
        if not cita:
            servicio = (
                Servicio.objects.filter(dentista=paciente.dentista)
                .order_by("id")
                .first()
            )
            if servicio:
                ahora = timezone.localtime()
                cita = Cita.objects.create(
                    dentista=paciente.dentista,
                    paciente=paciente,
                    servicio=servicio,
                    fecha=ahora.date(),
                    hora_inicio=ahora.time(),
                    hora_fin=(ahora + timedelta(minutes=30)).time(),
                    estado="INASISTENCIA",
                    notas="Penalización generada para pago en línea.",
                )
        if cita:
            penal_pago, creado = Pago.objects.get_or_create(
                cita=cita,
                defaults={
                    "monto": Decimal("300.00"),
                    "metodo": "EFECTIVO",
                    "estado": "PENDIENTE",
                },
            )
            if not creado and penal_pago.estado != "COMPLETADO":
                penal_pago.monto = Decimal("300.00")
                penal_pago.estado = "PENDIENTE"
                penal_pago.save(update_fields=["monto", "estado"])

    pagos = (
        Pago.objects.filter(cita__paciente=paciente)
        .select_related("cita", "cita__servicio")
        .order_by("-created_at")
    )
    pagos_pendientes = [p for p in pagos if p.estado == "PENDIENTE"]
    pagos_completados = [p for p in pagos if p.estado == "COMPLETADO"]

    return render(request, 'paciente/pagos.html', {
        'pagos_pendientes': pagos_pendientes,
        'pagos_completados': pagos_completados,
        'penal_info': penal_info,
    })


@login_required
def iniciar_pago(request, cita_id):
    """
    Crea la preferencia de MercadoPago y redirige al checkout.
    """
    try:
        paciente = request.user.paciente_perfil
    except Exception:
        return redirect('paciente:completar_perfil')

    pago = get_object_or_404(Pago, cita__id=cita_id, cita__paciente=paciente)
    if pago.estado == "COMPLETADO":
        messages.info(request, "Este pago ya está completado.")
        return redirect("paciente:mis_pagos")

    if request.method != "POST":
        messages.error(request, "Acción no permitida.")
        return redirect("paciente:mis_pagos")

    try:
        init_point = crear_preferencia_pago(pago.cita, request)
        # Guardamos método para saber que salió hacia MP
        pago.metodo = "MERCADOPAGO"
        pago.save(update_fields=["metodo"])
        return redirect(init_point)
    except Exception as exc:
        print(f"[MP] Error creando preferencia: {exc}")
        messages.error(request, "No se pudo iniciar el pago en línea. Revisa que tus credenciales de MercadoPago sean válidas y vuelve a intentar.")
        return redirect("paciente:mis_pagos")


@login_required
def pago_exitoso(request):
    """
    Callback de éxito de MercadoPago (sin webhook).
    Marca el pago como completado usando external_reference=cita_id.
    """
    ref = request.GET.get("external_reference") or request.GET.get("pref_id")
    try:
        cita_id = int(ref) if ref else None
    except (TypeError, ValueError):
        cita_id = None

    if not cita_id:
        messages.error(request, "No pudimos validar el pago (sin referencia).")
        return redirect("paciente:mis_pagos")

    pago = Pago.objects.filter(cita__id=cita_id, cita__paciente=request.user.paciente_perfil).first()
    if not pago:
        messages.error(request, "Pago no encontrado para esta cuenta.")
        return redirect("paciente:mis_pagos")

    previo = pago.estado
    if pago.estado != "COMPLETADO":
        pago.estado = "COMPLETADO"
        pago.metodo = pago.metodo or "MERCADOPAGO"
        pago.save(update_fields=["estado", "metodo"])
        _reactivar_paciente_si_penalizacion(pago)
        if previo != "COMPLETADO":
            try:
                crear_aviso_por_cita(
                    pago.cita,
                    "PAGO",
                    f"Pago aprobado (${pago.monto}) via {pago.metodo}",
                )
            except Exception as exc:
                print(f"[WARN] Aviso de pago exitoso no guardado: {exc}")

    params = urlencode({
        "pago_ok": 1,
        "servicio": pago.cita.servicio.nombre,
        "monto": str(pago.monto),
    })
    return redirect(f"{reverse('paciente:mis_pagos')}?{params}")


@login_required
def pago_fallido(request):
    messages.error(request, "El pago fue cancelado o falló.")
    return redirect("paciente:mis_pagos")


@login_required
def pago_pendiente(request):
    messages.info(request, "Pago en estado pendiente. Verifica más tarde.")
    return redirect("paciente:mis_pagos")


@csrf_exempt
def mp_webhook(request):
    """
    Webhook de MercadoPago para confirmar pagos.
    Valida el payment_id recibido y actualiza el Pago asociado a la cita (external_reference).
    """
    import json

    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido"}, status=405)

    # Token sencillo para descartar llamadas anónimas.
    expected_secret = getattr(settings, "MERCADOPAGO_WEBHOOK_SECRET", "")
    provided_secret = request.headers.get("X-WEBHOOK-SECRET") or request.GET.get("secret")
    if (not settings.DEBUG) and not expected_secret:
        return JsonResponse({"detail": "Webhook no configurado con secreto"}, status=403)
    if expected_secret and provided_secret != expected_secret:
        return JsonResponse({"detail": "Forbidden"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    topic = payload.get("type") or payload.get("action")
    if topic and "payment" not in str(topic).lower():
        return JsonResponse({"detail": "Evento no manejado"}, status=400)

    payment_id = payload.get("data", {}).get("id") or payload.get("id")
    if not payment_id:
        return JsonResponse({"detail": "Sin payment_id"}, status=400)

    if not getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", ""):
        return JsonResponse({"detail": "Access token no configurado"}, status=500)

    cache_key = f"mp:payment:{payment_id}"
    if cache.get(cache_key):
        return JsonResponse({"detail": "Evento ya procesado"}, status=200)

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    try:
        payment_info = sdk.payment().get(payment_id)
        status = payment_info.get("status")
        response = payment_info.get("response", {})
    except Exception as exc:
        print(f"[MP] Error consultando pago {payment_id}: {exc}")
        return JsonResponse({"detail": "Error consultando pago"}, status=500)

    if status != 200:
        return JsonResponse({"detail": f"Estado HTTP {status}"}, status=400)

    mp_status = response.get("status")
    ext_ref = response.get("external_reference")
    if not ext_ref:
        return JsonResponse({"detail": "Sin external_reference"}, status=400)
    try:
        ext_ref_int = int(ext_ref)
    except Exception:
        return JsonResponse({"detail": "external_reference inválido"}, status=400)

    pago = Pago.objects.filter(cita__id=ext_ref_int).first()
    if not pago:
        return JsonResponse({"detail": "Pago no encontrado"}, status=404)

    previo = pago.estado
    # Validar monto contra el pago registrado
    mp_amount = response.get("transaction_amount")
    if mp_amount is not None:
        try:
            mp_val = Decimal(str(mp_amount))
            pago_val = Decimal(str(pago.monto))
            # Permitimos pequeñas variaciones (< $0.05) por redondeos/impuestos
            if abs(mp_val - pago_val) > Decimal("0.05"):
                return JsonResponse({"detail": "Monto inconsistente"}, status=400)
        except Exception:
            if settings.DEBUG:
                print(f"[MP] No se pudo validar monto de MP={mp_amount} contra pago={pago.monto}")

    if mp_status in ("approved", "authorized"):
        pago.estado = "COMPLETADO"
        pago.metodo = "MERCADOPAGO"
        pago.save(update_fields=["estado", "metodo"])
        cache.set(cache_key, True, timeout=3600)
        _reactivar_paciente_si_penalizacion(pago)
        if previo != "COMPLETADO":
            try:
                crear_aviso_por_cita(
                    pago.cita,
                    "PAGO",
                    f"Pago aprobado (${pago.monto}) via MercadoPago",
                )
            except Exception as exc:
                print(f"[WARN] Aviso de webhook no guardado: {exc}")
        return JsonResponse({"detail": "Pago confirmado"}, status=200)

    # Otros estados: pending, in_process, rejected...
    if mp_status in ("pending", "in_process"):
        pago.estado = "PENDIENTE"
        pago.metodo = "MERCADOPAGO"
        pago.save(update_fields=["estado", "metodo"])
        cache.set(cache_key, True, timeout=900)
        return JsonResponse({"detail": "Pago en proceso"}, status=202)

    return JsonResponse({"detail": f"Estado no aprobado: {mp_status}"}, status=200)


@login_required
def pagar_penalizacion(request):
    try:
        paciente = request.user.paciente_perfil
    except Paciente.DoesNotExist:
        return redirect("paciente:completar_perfil")

    info = calcular_penalizacion_paciente(paciente)
    penal_pendiente = (
        Pago.objects.filter(
            cita__paciente=paciente,
            cita__estado="INASISTENCIA",
            estado="PENDIENTE",
            monto__gte=Decimal("300"),
        )
        .order_by("-created_at")
        .first()
    )

    if info["estado"] in ["sin_penalizacion", "warning"]:
        messages.info(request, "No tienes penalizaciones por cubrir.")
        return redirect("paciente:dashboard")

    if request.method == "POST":
        if penal_pendiente and penal_pendiente.estado != "COMPLETADO":
            penal_pendiente.estado = "COMPLETADO"
            penal_pendiente.save(update_fields=["estado"])

        if penal_pendiente:
            _reactivar_paciente_si_penalizacion(penal_pendiente)

        messages.success(
            request,
            "Pago registrado. Si tu cuenta estaba suspendida por penalización, se reactivó automáticamente.",
        )
        return redirect("paciente:dashboard")

    return render(
        request,
        "paciente/pagar_penalizacion.html",
        {"penalizacion": info, "penal_pendiente": penal_pendiente},
    )

@login_required
def cancelar_registro_paciente(request):
    logout(request)
    return redirect('home')


@login_required
def cancelar_cita(request, cita_id):
    try:
        paciente = request.user.paciente_perfil
    except Paciente.DoesNotExist:
        return redirect('paciente:completar_perfil')

    if request.method != "POST":
        return redirect("paciente:dashboard")

    cita = get_object_or_404(Cita, id=cita_id, paciente=paciente)

    hoy = timezone.localdate()
    canceladas_mes = Cita.objects.filter(
        paciente=paciente,
        estado="CANCELADA",
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).exclude(id=cita_id).count()
    if canceladas_mes > 0:
        messages.error(request, "Ya usaste tu cancelación de este mes. Contacta a tu dentista para más cambios.")
        return redirect("paciente:dashboard")

    if cita.estado == "CANCELADA":
        messages.info(request, "La cita ya estaba cancelada.")
        return redirect("paciente:dashboard")
    if cita.estado == "INASISTENCIA":
        messages.error(request, "No puedes cancelar una cita ya marcada como inasistencia.")
        return redirect("paciente:dashboard")

    # Si tiene un pago pendiente, lo eliminamos al cancelar la cita
    try:
        pago_rel = getattr(cita, "pago_relacionado", None)
        if pago_rel and pago_rel.estado != "COMPLETADO":
            pago_rel.delete()
    except Exception as e:
        print(f"[WARN] No se pudo limpiar pago pendiente al cancelar cita: {e}")

    cita.estado = "CANCELADA"
    cita.save(update_fields=["estado"])
    try:
        crear_aviso_por_cita(cita, "CANCELADA", "Cita cancelada por el paciente")
    except Exception as e:
        print(f"[WARN] No se pudo crear aviso de cancelación: {e}")

    messages.success(request, "Cita cancelada. Se notificará al dentista.")
    return redirect("paciente:dashboard")


@login_required
@require_POST
def contactar_dentista(request):
    """
    Envía un correo de contacto al buzón del consultorio.
    """
    try:
        paciente = request.user.paciente_perfil
    except Exception:
        return JsonResponse({"status": "error", "msg": "Perfil de paciente no encontrado."}, status=400)

    destino = "dentista.choyo@gmail.com"
    remitente = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    if not remitente:
        return JsonResponse({"status": "error", "msg": "Sin remitente configurado."}, status=500)

    asunto = f"Contacto de paciente: {paciente.nombre}"
    mensaje = (
        f"Paciente: {paciente.nombre}\n"
        f"Email: {getattr(request.user, 'email', 'N/D')}\n"
        f"Teléfono: {paciente.telefono or 'N/D'}\n"
        f"Mensaje: El paciente solicita contacto con su especialista."
    )
    try:
        send_mail(asunto, mensaje, remitente, [destino], fail_silently=False)
        return JsonResponse({"status": "ok"})
    except Exception as exc:
        return JsonResponse({"status": "error", "msg": str(exc)}, status=500)


@login_required
def feedback_cita(request, cita_id):
    try:
        paciente = request.user.paciente_perfil
    except Exception:
        return redirect("paciente:completar_perfil")

    cita = get_object_or_404(Cita, id=cita_id, paciente=paciente)
    feedback = (
        EncuestaSatisfaccion.objects.filter(paciente=paciente, cita=cita)
        .order_by("-created_at")
        .first()
    )

    if request.method == "POST":
        puntuacion_raw = request.POST.get("puntuacion", "5")
        comentario = request.POST.get("comentario", "").strip()

        try:
            puntuacion = max(1, min(5, int(puntuacion_raw)))
        except ValueError:
            puntuacion = 5

        feedback, _ = EncuestaSatisfaccion.objects.update_or_create(
            paciente=paciente,
            dentista=cita.dentista,
            cita=cita,
            defaults={"puntuacion": puntuacion, "comentario": comentario},
        )

        tono = "positivo" if puntuacion >= 4 else "neutral" if puntuacion == 3 else "negativo"
        resumen = comentario or f"Experiencia {tono}"
        messages.success(request, f"¡Gracias por tu opinión! Resumen IA: {resumen[:140]}")
        return redirect("paciente:dashboard")

    return render(
        request,
        "paciente/feedback_cita.html",
        {"cita": cita, "feedback": feedback},
    )


@login_required
def confirmar_por_email(request, token):
    signer = TimestampSigner()
    try:
        cita_id = signer.unsign(token, max_age=60 * 60 * 24 * 7)  # 7 días
    except (BadSignature, SignatureExpired):
        messages.error(request, "Enlace inválido o expirado.")
        return redirect("paciente:dashboard")

    cita = get_object_or_404(Cita, id=cita_id, paciente=request.user.paciente_perfil)
    if cita.estado != "CONFIRMADA":
        cita.estado = "CONFIRMADA"
        cita.save(update_fields=["estado"])
        messages.success(request, "Asistencia confirmada. ¡Te esperamos!")
    else:
        messages.info(request, "La cita ya estaba confirmada.")
    return redirect("paciente:dashboard")


@login_required
def recibo_pago_pdf(request, pago_id):
    paciente = getattr(request.user, "paciente_perfil", None)
    if not paciente:
        return redirect("paciente:dashboard")

    pago = get_object_or_404(
        Pago.objects.select_related("cita", "cita__servicio", "cita__dentista", "cita__paciente"),
        id=pago_id,
        cita__paciente=paciente,
    )

    def _esc(text):
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def t_line(x, y, text, size=12, color=(0, 0, 0)):
        r, g, b = color
        return f"BT /F1 {size} Tf {r:.3f} {g:.3f} {b:.3f} rg 1 0 0 1 {x} {y} Tm ({_esc(text)}) Tj ET\n"

    def rect(x, y, w, h, fill_color=None, stroke_color=None, stroke_width=1):
        ops = ""
        if fill_color:
            r, g, b = fill_color
            ops += f"{r:.3f} {g:.3f} {b:.3f} rg "
        if stroke_color:
            r, g, b = stroke_color
            ops += f"{r:.3f} {g:.3f} {b:.3f} RG "
        ops += f"{stroke_width:.2f} w {x} {y} {w} {h} re "
        if fill_color and stroke_color:
            ops += "B\n"
        elif fill_color:
            ops += "f\n"
        elif stroke_color:
            ops += "S\n"
        return ops

    width, height = 595, 842
    card_x, card_y = 70, 180
    card_w, card_h = width - 2 * card_x, 520
    header_h = 82

    content = ""
    # Fondo y tarjeta
    content += rect(card_x - 8, card_y - 10, card_w + 16, card_h + 26, fill_color=(0.04, 0.07, 0.12), stroke_color=(0.28, 0.5, 0.85), stroke_width=2.2)
    content += rect(card_x, card_y, card_w, card_h, fill_color=(0.055, 0.09, 0.16), stroke_color=(0.32, 0.55, 0.9), stroke_width=2)

    # Header
    content += rect(card_x + 6, card_y + card_h - header_h, card_w - 12, header_h - 12, fill_color=(0.35, 0.62, 0.96), stroke_color=(0.9, 0.96, 1), stroke_width=1.6)
    content += t_line(card_x + 20, card_y + card_h - 32, "Recibo de pago", size=20, color=(1, 1, 1))
    content += t_line(card_x + 20, card_y + card_h - 52, f"Emitido: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}", size=11, color=(0.9, 0.95, 1))
    content += t_line(card_x + card_w - 120, card_y + card_h - 32, f"Folio #{pago.id}", size=12, color=(0.96, 0.98, 1))

    # Datos del paciente
    info_w = card_w - 24
    info_h = 230
    info_x = card_x + 12
    info_y = card_y + card_h - header_h - info_h - 10
    content += rect(info_x, info_y, info_w, info_h, fill_color=(0.98, 0.99, 1), stroke_color=(0.76, 0.86, 1), stroke_width=1.4)
    y_text = info_y + info_h - 28
    content += t_line(info_x + 12, y_text, "Datos del paciente", size=13, color=(0.1, 0.16, 0.32)); y_text -= 22
    content += t_line(info_x + 12, y_text, f"Paciente: {pago.cita.paciente.nombre}", size=12, color=(0.05, 0.08, 0.18)); y_text -= 18
    content += t_line(info_x + 12, y_text, f"Dentista: {pago.cita.dentista.nombre}", size=12, color=(0.05, 0.08, 0.18)); y_text -= 18
    content += t_line(info_x + 12, y_text, f"Servicio: {pago.cita.servicio.nombre}", size=12, color=(0.05, 0.08, 0.18)); y_text -= 18
    content += t_line(info_x + 12, y_text, f"Fecha cita: {pago.cita.fecha.strftime('%d/%m/%Y')} {pago.cita.hora_inicio.strftime('%H:%M')}", size=12, color=(0.05, 0.08, 0.18))

    # Resumen de pago (abajo)
    summary_h = 120
    summary_x = card_x + 12
    summary_y = card_y + 28
    content += rect(summary_x, summary_y, info_w, summary_h, fill_color=(0.93, 0.97, 1), stroke_color=(0.75, 0.86, 1), stroke_width=1.3)
    col1 = summary_x + 16
    col2 = summary_x + 200
    col3 = summary_x + 360
    content += t_line(col1, summary_y + summary_h - 30, "Monto", size=12, color=(0.1, 0.16, 0.32))
    content += t_line(col1, summary_y + summary_h - 56, f"${pago.monto:.2f} MXN", size=18, color=(0.05, 0.45, 0.22))
    content += t_line(col2, summary_y + summary_h - 30, "Método", size=12, color=(0.1, 0.16, 0.32))
    content += t_line(col2, summary_y + summary_h - 56, pago.metodo.upper(), size=13, color=(0.05, 0.08, 0.18))
    content += t_line(col3, summary_y + summary_h - 30, "Estado", size=12, color=(0.1, 0.16, 0.32))
    estado_color = (0.05, 0.55, 0.32) if pago.estado.upper() == "COMPLETADO" else (0.9, 0.55, 0.1)
    content += t_line(col3, summary_y + summary_h - 56, pago.estado.title(), size=13, color=estado_color)

    # Nota
    content += t_line(card_x - 4, 108, "Gracias por tu pago. Conserva este recibo como comprobante.", size=11, color=(0.25, 0.35, 0.55))

    stream_bytes = content.encode("latin-1", "ignore")

    obj_catalog = b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    obj_pages = b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
    obj_page = b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >> endobj\n"
    obj_font = b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    obj_content = f"5 0 obj << /Length {len(stream_bytes)} >> stream\n".encode() + stream_bytes + b"\nendstream endobj\n"

    parts = [b"%PDF-1.4\n", obj_catalog, obj_pages, obj_page, obj_font, obj_content]
    offsets = []
    cursor = 0
    for p in parts:
        offsets.append(cursor)
        cursor += len(p)
    xref_start = cursor

    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref_start).encode() + b"\n%%EOF"

    pdf_bytes = b"".join(parts) + xref + trailer
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename=\"recibo_pago_{pago.id}.pdf\"'
    return response


@login_required
def reprogramar_cita(request, cita_id):
    try:
        paciente = request.user.paciente_perfil
    except:
        return redirect('paciente:completar_perfil')

    cita = get_object_or_404(Cita, id=cita_id, paciente=paciente)
    if request.method != "POST":
        return redirect("paciente:dashboard")

    hoy = timezone.localdate()
    reprogramadas_mes = Cita.objects.filter(
        paciente=paciente,
        veces_reprogramada__gte=1,
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).exclude(id=cita_id).count()
    if reprogramadas_mes > 0:
        messages.error(request, "Ya usaste tu reprogramación de este mes. Comunícate con tu dentista para más cambios.")
        return redirect("paciente:dashboard")

    # Regla: solo una reprogramación por cita
    if getattr(cita, "veces_reprogramada", 0) >= 1:
        messages.error(request, "Ya reprogramaste esta cita. Comunícate con tu dentista para más cambios.")
        return redirect("paciente:dashboard")

    fecha_str = request.POST.get("fecha")
    hora_str = request.POST.get("hora")
    if not fecha_str or not hora_str:
        messages.error(request, "Fecha u hora inválidas.")
        return redirect("paciente:dashboard")

    try:
        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hora_inicio = datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        messages.error(request, "Formato de fecha u hora inválido.")
        return redirect("paciente:dashboard")

    hoy = timezone.localdate()
    limite = hoy + timedelta(days=60)
    if fecha_obj < hoy:
        messages.error(request, "No puedes reprogramar a una fecha pasada.")
        return redirect("paciente:dashboard")
    if fecha_obj > limite:
        messages.error(request, "Solo puedes reprogramar hasta 60 días a partir de hoy.")
        return redirect("paciente:dashboard")
    if fecha_obj.weekday() == 6:
        messages.error(request, "No se atiende los domingos. Elige otro día.")
        return redirect("paciente:dashboard")

    inicio_dt = datetime.combine(fecha_obj, hora_inicio)
    fin_dt = inicio_dt + timedelta(minutes=cita.servicio.duracion_estimada or 30)

    now_local = timezone.localtime()
    if fecha_obj == now_local.date() and hora_inicio <= now_local.time():
        messages.error(request, "No puedes reprogramar a una hora que ya pasó.")
        return redirect("paciente:dashboard")

    # Validar disponibilidad (permitimos el mismo slot original para evitar bloquear reprogramar sin cambios)
    slots_libres = set(
        obtener_slots_disponibles(
            cita.dentista,
            fecha_obj,
            cita.servicio,
            minutos_bloque=15,
        )
    )
    slot_key = hora_inicio.strftime("%H:%M")
    slot_actual = cita.hora_inicio.strftime("%H:%M")
    if slot_key not in slots_libres and not (
        cita.fecha == fecha_obj and slot_key == slot_actual
    ):
        messages.error(request, "Ese horario ya no está disponible. Elige otro.")
        return redirect("paciente:dashboard")

    cita.fecha = fecha_obj
    cita.hora_inicio = hora_inicio
    cita.hora_fin = fin_dt.time()
    cita.estado = "PENDIENTE"
    cita.veces_reprogramada = getattr(cita, "veces_reprogramada", 0) + 1
    cita.recordatorio_24h_enviado = False
    cita.save(update_fields=[
        "fecha",
        "hora_inicio",
        "hora_fin",
        "estado",
        "veces_reprogramada",
        "recordatorio_24h_enviado",
    ])

    try:
        crear_aviso_por_cita(cita, "REPROGRAMADA", "Cita reprogramada por el paciente")
    except Exception as e:
        print(f"[WARN] No se pudo crear aviso de reprogramación: {e}")

    try:
        enviar_correo_confirmacion_cita(cita)
    except Exception as e:
        print(f"[WARN] No se pudo enviar correo de reprogramación: {e}")

    messages.success(request, "Cita reprogramada correctamente.")
    return redirect("paciente:dashboard")


# ========================================================
# API DE SLOTS PARA PACIENTE (por servicio)
# ========================================================
def api_slots(request):
    fecha_str = request.GET.get("fecha")
    servicio_id = request.GET.get("servicio_id")
    if not fecha_str or not servicio_id:
        return JsonResponse({"slots": [], "msg": "Faltan parámetros"}, status=400)

    try:
        servicio = Servicio.objects.get(id=servicio_id)
    except Servicio.DoesNotExist:
        return JsonResponse({"slots": [], "msg": "Servicio no encontrado"}, status=404)

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"slots": [], "msg": "Fecha inválida"}, status=400)

    hoy = timezone.localdate()
    limite = hoy + timedelta(days=60)
    if fecha < hoy:
        return JsonResponse({"slots": [], "msg": "No se permiten fechas pasadas"}, status=400)
    if fecha > limite:
        return JsonResponse({"slots": [], "msg": "Fuera de rango (60 días)"}, status=400)
    if fecha.weekday() == 6:
        return JsonResponse({"slots": [], "msg": "No se atiende domingos"}, status=400)

    dentista = servicio.dentista
    horarios = Horario.objects.filter(dentista=dentista, dia_semana=fecha.isoweekday())
    if not horarios:
        return JsonResponse({"slots": [], "msg": "Día no laboral"})

    # Usamos la misma lógica centralizada de domain.ai_services para calcular libres
    libres = set(obtener_slots_disponibles(dentista, fecha, servicio, minutos_bloque=15))

    slots = []
    ahora = timezone.localtime()
    duracion = servicio.duracion_estimada or 30
    for h in horarios:
        cursor = datetime.combine(fecha, h.hora_inicio)
        fin = datetime.combine(fecha, h.hora_fin)
        while cursor + timedelta(minutes=duracion) <= fin:
            label = cursor.strftime("%H:%M")
            if fecha > hoy or cursor.time() > ahora.time():
                slots.append({
                    "hora": label,
                    "estado": "libre" if label in libres else "ocupado",
                    "recomendado": False
                })
            cursor += timedelta(minutes=15)

    for s in slots:
        if s["estado"] == "libre":
            s["recomendado"] = True
            break

    return JsonResponse({"slots": slots})
