import json
import os
import hmac
from datetime import datetime, timedelta
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db import models
from rest_framework import generics, permissions, serializers
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication

# IMPORTANTE: Importamos los modelos correctos desde 'domain'
# Agregamos 'Dentista' para poder buscarlo por ID
from domain.models import Servicio, Horario, Dentista
from domain.notifications import enviar_correo_confirmacion_cita
from domain.ai_services import (
    obtener_slots_disponibles,
    calcular_penalizacion_paciente,
)
from domain.models import Cita, Pago

# Servicios auxiliares con fallback
try:
    from paciente.services import crear_aviso_por_cita
except Exception:
    def crear_aviso_por_cita(*args, **kwargs):
        return None

# Chatbot IA / fallback
try:
    from domain.ai_chatbot import responder_chatbot
except Exception:
    responder_chatbot = None


# ---------------------------------------------------------
# Healthcheck simple
# ---------------------------------------------------------
@api_view(["GET"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """Devuelve estado básico y, si se proporciona token, info extendida."""
    token = request.headers.get("X-HEALTH-TOKEN")
    expected = os.getenv("HEALTH_TOKEN")
    payload = {
        "status": "ok",
        "time": timezone.now().isoformat(),
    }
    if expected and token and hmac.compare_digest(token, expected):
        payload["cache_backend"] = settings.CACHES["default"]["BACKEND"]
        payload["allowed_hosts"] = settings.ALLOWED_HOSTS
        payload["secure_proxy_ssl_header"] = settings.SECURE_PROXY_SSL_HEADER
    return Response(payload)


# ---------------------------------------------------------
# Serializer DRF para Servicio (para la API de servicios)
# ---------------------------------------------------------
class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ("id", "nombre", "precio", "duracion_estimada", "activo")


# ---------------------------------------------------------
# Lista de servicios activos
# ---------------------------------------------------------
class ServicioListAPIView(generics.ListAPIView):
    """
    API para listar los servicios activos del consultorio.
    El frontend puede consumirla para llenar selects, etc.
    """
    queryset = Servicio.objects.filter(activo=True).order_by("nombre")
    serializer_class = ServicioSerializer
    permission_classes = [permissions.AllowAny]


# ---------------------------------------------------------
# Chatbot
# ---------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET", "POST"])
def chatbot_api(request):
    """
    API que recibe mensajes del chat y devuelve respuestas.
    Espera JSON: {"query": "texto del usuario"}
    Responde: {"message": "respuesta del bot"}
    """
    # IP real (respeta X-Forwarded-For si existe)
    ip = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "anon")

    # Token opcional para uso público controlado
    expected_secret = getattr(settings, "CHATBOT_API_SECRET", "")
    require_secret = bool(getattr(settings, "CHATBOT_REQUIRE_SECRET", not settings.DEBUG))
    provided_secret = request.headers.get("X-CHATBOT-SECRET")
    if require_secret and not expected_secret:
        return JsonResponse({"message": "Service not configured"}, status=503)
    if expected_secret and not (provided_secret and hmac.compare_digest(provided_secret, expected_secret)):
        print(f"[CHATBOT] Forbidden secret from IP {ip}")
        return JsonResponse({"message": "Forbidden"}, status=403)

    # Freno simple por IP para evitar abuso.
    key = f"chatbot:rate:{ip}"
    hits = cache.get(key, 0)
    max_hits = int(getattr(settings, "CHATBOT_RATE_LIMIT_MAX", 20))
    window = int(getattr(settings, "CHATBOT_RATE_LIMIT_WINDOW", 60))
    if hits >= max_hits:
        print(f"[CHATBOT] Throttle IP {ip} ({hits} req/min)")
        return JsonResponse({"message": "Too many requests. Try again later."}, status=429)
    cache.set(key, hits + 1, timeout=window)

    try:
        if request.method == "GET":
            mensaje = (request.GET.get("query") or "").strip()
            if not mensaje:
                return JsonResponse(
                    {"message": "Usa POST con JSON {'query': '...'} o GET ?query=texto."},
                    status=200,
                )
        else:
            data = json.loads(request.body)
            mensaje = data.get("query", "").strip()

            if not mensaje:
                return JsonResponse({"message": "Request body requires 'query'."}, status=400)

        # Historial breve por sesión (anónimo o logueado).
        history = []
        try:
            history = request.session.get("chatbot_history", []) or []
        except Exception:
            history = []

        lang = getattr(request, "LANGUAGE_CODE", "es") or "es"
        if responder_chatbot:
            payload = responder_chatbot(mensaje, history=history, lang_code=lang)
            respuesta = payload.get("message")
            source = payload.get("source", "local")
            source_detail = payload.get("source_detail")
        else:
            # Fallback mínimo si el módulo no está disponible
            respuesta = "Soy el asistente RC. Puedo ayudarte con horarios, pagos y penalizaciones. Cuéntame tu duda."
            source = "local"
            source_detail = None

        # Guardar historial (máx 6 mensajes combinados User/Bot)
        try:
            history.append(f"Usuario: {mensaje}")
            history.append(f"Asistente: {respuesta}")
            request.session["chatbot_history"] = history[-6:]
            request.session.modified = True
        except Exception:
            pass
        resp_payload = {"message": respuesta, "source": source}
        if source_detail:
            resp_payload["source_detail"] = source_detail
        # Log ligero sin datos sensibles
        print(f"[CHATBOT] ip={ip} source={source} hits={hits+1}")
        return JsonResponse(resp_payload)

    except json.JSONDecodeError:
        return JsonResponse({"message": "Error de formato JSON."}, status=400)
    except Exception as e:
        print(f"[chatbot_api] Error interno: {e}")
        return JsonResponse({"message": "Internal error."}, status=500)


# ---------------------------------------------------------
# Slots disponibles para una fecha / servicio
# ---------------------------------------------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def api_slots_disponibles(request):
    """
    Endpoint para obtener slots de agenda disponibles.

    Parámetros GET:
      - fecha (YYYY-MM-DD)    [obligatorio]
      - servicio_id           [obligatorio]
      - dentista_id           [opcional]

    Si NO viene dentista_id:
      - Se usa request.user.perfil_dentista (si existe).

    Respuesta:
      { "slots": ["09:00", "09:15", ...] }
    """
    fecha_str = request.GET.get("fecha")
    servicio_id = request.GET.get("servicio_id")
    dentista_id = request.GET.get("dentista_id")

    # ---------------- Validaciones básicas ----------------
    if not fecha_str or not servicio_id:
        return JsonResponse(
            {"detail": "Parámetros incompletos: fecha y servicio_id son obligatorios."},
            status=400,
        )

    fecha = parse_date(fecha_str)
    if not fecha:
        return JsonResponse(
            {"detail": "Fecha inválida. Usa formato YYYY-MM-DD."},
            status=400,
        )

    hoy = timezone.localdate()
    limite = hoy + timezone.timedelta(days=60)
    if fecha < hoy:
        return JsonResponse({"detail": "No se permiten fechas pasadas."}, status=400)
    if fecha > limite:
        return JsonResponse({"detail": "Fuera de rango (60 días)."}, status=400)
    if fecha.isoweekday() == 7:
        return JsonResponse({"detail": "No se atiende los domingos."}, status=400)

    # ---------------- Resolver dentista ----------------
    if dentista_id:
        # CORRECCIÓN AQUÍ:
        # Antes buscabas en 'Disponibilidad', ahora buscamos directo en 'Dentista'
        dentista = Dentista.objects.filter(id=dentista_id).first()
        
        if not dentista:
            return JsonResponse(
                {"detail": "Dentista no encontrado."},
                status=404,
            )
    else:
        # Intentamos obtener el dentista del usuario logueado
        # Nota: En tu modelo Dentista la relación es 'dentista' (related_name='dentista' o 'perfil_dentista')
        # Ajusta según tu models.py. Usaré lo común:
        dentista = getattr(request.user, "dentista", None)

        if dentista is None:
            return JsonResponse(
                {"detail": "No se pudo determinar el dentista."},
                status=400,
            )

    # ---------------- Obtener servicio ----------------
    servicio = Servicio.objects.filter(id=servicio_id, activo=True).first()
    if not servicio:
        return JsonResponse(
            {"detail": "Servicio no encontrado o inactivo."},
            status=404,
        )

    # ---------------- Calcular slots ----------------
    # Esta función debe venir de tu 'domain/ai_services.py'
    try:
        slots = obtener_slots_disponibles(dentista, fecha, servicio)
        if not slots:
            return JsonResponse({"slots": [], "detail": "Sin horarios disponibles para esa fecha."})
        return JsonResponse({"slots": slots})
    except Exception as e:
        print(f"Error calculando slots: {e}")
        return JsonResponse({"slots": []})


# ---------------------------------------------------------
# Crear cita (API móvil)
# ---------------------------------------------------------
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def api_crear_cita(request):
    """
    Crea una cita para el paciente autenticado.
    Espera JSON:
      {
        "servicio_id": 1,
        "fecha": "2025-01-15",
        "hora": "09:30"
      }
    Responde 201 con info básica de la cita.
    """
    user = request.user
    if not hasattr(user, "paciente_perfil"):
        return Response({"detail": "Perfil de paciente requerido."}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data or {}
    servicio_id = data.get("servicio_id")
    fecha_str = data.get("fecha")
    hora_str = data.get("hora")

    if not (servicio_id and fecha_str and hora_str):
        return Response({"detail": "servicio_id, fecha y hora son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

    paciente = user.paciente_perfil
    penal_info = calcular_penalizacion_paciente(paciente)
    if penal_info.get("estado") in ["pending", "disabled"]:
        return Response(
            {"detail": "No puedes agendar hasta cubrir la penalización pendiente ($300)."},
            status=status.HTTP_403_FORBIDDEN,
        )

    servicio = Servicio.objects.filter(id=servicio_id, activo=True).first()
    if not servicio:
        return Response({"detail": "Servicio no encontrado o inactivo."}, status=status.HTTP_404_NOT_FOUND)

    try:
        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"detail": "Fecha inválida (YYYY-MM-DD)."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        hora_inicio = datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        return Response({"detail": "Hora inválida (HH:MM)."}, status=status.HTTP_400_BAD_REQUEST)

    hoy = timezone.localdate()
    limite = hoy + timedelta(days=60)
    if fecha_obj < hoy:
        return Response({"detail": "No se permiten fechas pasadas."}, status=status.HTTP_400_BAD_REQUEST)
    if fecha_obj > limite:
        return Response({"detail": "Solo se permite agendar 60 días hacia adelante."}, status=status.HTTP_400_BAD_REQUEST)
    if fecha_obj.weekday() == 6:
        return Response({"detail": "No se atiende los domingos."}, status=status.HTTP_400_BAD_REQUEST)

    now_local = timezone.localtime()
    if fecha_obj == now_local.date() and hora_inicio <= now_local.time():
        return Response({"detail": "No puedes agendar en una hora que ya pasó."}, status=status.HTTP_400_BAD_REQUEST)

    dentista = servicio.dentista
    duracion = servicio.duracion_estimada or 30
    fin_dt = datetime.combine(fecha_obj, hora_inicio) + timedelta(minutes=duracion)

    slots_libres = set(
        obtener_slots_disponibles(
            dentista,
            fecha_obj,
            servicio,
            minutos_bloque=15,
        )
    )
    slot_key = hora_inicio.strftime("%H:%M")
    if slot_key not in slots_libres:
        return Response({"detail": "Ese horario ya no está disponible."}, status=status.HTTP_409_CONFLICT)

    cita = paciente.cita_set.create(
        dentista=dentista,
        servicio=servicio,
        fecha=fecha_obj,
        hora_inicio=hora_inicio,
        hora_fin=fin_dt.time(),
        estado="PENDIENTE",
    )

    try:
        Pago.objects.get_or_create(
            cita=cita,
            defaults={
                "monto": servicio.precio,
                "metodo": "MERCADOPAGO",
                "estado": "PENDIENTE",
            },
        )
    except Exception as exc:
        print(f"[WARN] No se pudo crear pago pendiente: {exc}")

    try:
        enviar_correo_confirmacion_cita(cita)
    except Exception as exc:
        print(f"[WARN] No se pudo enviar correo de confirmación: {exc}")

    try:
        crear_aviso_por_cita(
            cita,
            "NUEVA_CITA",
            f"Cita solicitada desde la app móvil: {servicio.nombre}",
        )
    except Exception as exc:
        print(f"[WARN] No se pudo crear aviso: {exc}")

    return Response(
        {
            "id": cita.id,
            "servicio": {"id": servicio.id, "nombre": servicio.nombre},
            "fecha": fecha_obj.isoformat(),
            "hora": slot_key,
            "estado": cita.estado,
            "dentista": {"id": dentista.id, "nombre": dentista.nombre},
        },
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------
# Listar citas (próximas e historial)
# ---------------------------------------------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def api_listar_citas(request):
    """
    Devuelve próximas citas (PENDIENTE/CONFIRMADA futuras) e historial (pasadas/canceladas).
    """
    user = request.user
    if not hasattr(user, "paciente_perfil"):
        return Response({"detail": "Perfil de paciente requerido."}, status=status.HTTP_400_BAD_REQUEST)

    paciente = user.paciente_perfil
    hoy = timezone.localdate()
    now_time = timezone.localtime().time()

    proximas_qs = (
        Cita.objects.filter(
            paciente=paciente,
            estado__in=["PENDIENTE", "CONFIRMADA"]
        )
        .filter(models.Q(fecha__gt=hoy) | models.Q(fecha=hoy, hora_inicio__gte=now_time))
        .select_related("servicio", "dentista")
        .order_by("fecha", "hora_inicio")
    )

    historial_qs = (
        Cita.objects.filter(paciente=paciente)
        .exclude(id__in=proximas_qs.values_list("id", flat=True))
        .select_related("servicio", "dentista")
        .order_by("-fecha", "-hora_inicio")[:10]
    )

    def serialize_cita(c):
        return {
            "id": c.id,
            "servicio": {"id": c.servicio_id, "nombre": c.servicio.nombre},
            "fecha": c.fecha.isoformat(),
            "hora": c.hora_inicio.strftime("%H:%M"),
            "estado": c.estado,
            "dentista": {"id": c.dentista_id, "nombre": c.dentista.nombre},
            "puede_reprogramar": c.estado in ["PENDIENTE", "CONFIRMADA"],
            "puede_cancelar": c.estado in ["PENDIENTE", "CONFIRMADA"],
        }

    return Response(
        {
            "proximas": [serialize_cita(c) for c in proximas_qs],
            "historial": [serialize_cita(c) for c in historial_qs],
        }
    )


# ---------------------------------------------------------
# Cancelar cita
# ---------------------------------------------------------
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def api_cancelar_cita(request, cita_id: int):
    user = request.user
    if not hasattr(user, "paciente_perfil"):
        return Response({"detail": "Perfil de paciente requerido."}, status=status.HTTP_400_BAD_REQUEST)

    paciente = user.paciente_perfil
    cita = Cita.objects.filter(id=cita_id, paciente=paciente).select_related("servicio", "dentista").first()
    if not cita:
        return Response({"detail": "Cita no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    if cita.estado not in ["PENDIENTE", "CONFIRMADA"]:
        return Response({"detail": "La cita no puede cancelarse."}, status=status.HTTP_400_BAD_REQUEST)

    # Penalizaciones y reglas simples: no permitir cancelar si es misma hora
    ahora = timezone.localtime()
    if cita.fecha == ahora.date() and cita.hora_inicio <= ahora.time():
        return Response({"detail": "No puedes cancelar una cita que ya inició o pasó."}, status=status.HTTP_400_BAD_REQUEST)

    cita.estado = "CANCELADA"
    cita.save(update_fields=["estado"])

    try:
        crear_aviso_por_cita(cita, "CANCELADA", "Cita cancelada desde la app móvil.")
    except Exception as exc:
        print(f"[WARN] No se pudo crear aviso cancelación: {exc}")

    return Response(
        {
            "id": cita.id,
            "estado": cita.estado,
            "servicio": {"id": cita.servicio_id, "nombre": cita.servicio.nombre},
            "fecha": cita.fecha.isoformat(),
            "hora": cita.hora_inicio.strftime("%H:%M"),
        }
    )


# ---------------------------------------------------------
# Reprogramar cita
# ---------------------------------------------------------
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def api_reprogramar_cita(request, cita_id: int):
    """
    Requiere JSON: {"fecha": "YYYY-MM-DD", "hora": "HH:MM"}
    """
    user = request.user
    if not hasattr(user, "paciente_perfil"):
        return Response({"detail": "Perfil de paciente requerido."}, status=status.HTTP_400_BAD_REQUEST)

    paciente = user.paciente_perfil
    cita = Cita.objects.filter(id=cita_id, paciente=paciente).select_related("servicio", "dentista").first()
    if not cita:
        return Response({"detail": "Cita no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    if cita.estado not in ["PENDIENTE", "CONFIRMADA"]:
        return Response({"detail": "La cita no puede reprogramarse."}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data or {}
    fecha_str = data.get("fecha")
    hora_str = data.get("hora")
    if not (fecha_str and hora_str):
        return Response({"detail": "fecha y hora son obligatorias."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        nueva_fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        nueva_hora = datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        return Response({"detail": "Formato de fecha u hora inválido."}, status=status.HTTP_400_BAD_REQUEST)

    hoy = timezone.localdate()
    limite = hoy + timedelta(days=60)
    if nueva_fecha < hoy:
        return Response({"detail": "No se permiten fechas pasadas."}, status=status.HTTP_400_BAD_REQUEST)
    if nueva_fecha > limite:
        return Response({"detail": "Fuera de rango (60 días)."}, status=status.HTTP_400_BAD_REQUEST)
    if nueva_fecha.weekday() == 6:
        return Response({"detail": "No se atiende domingos."}, status=status.HTTP_400_BAD_REQUEST)

    now_local = timezone.localtime()
    if nueva_fecha == now_local.date() and nueva_hora <= now_local.time():
        return Response({"detail": "No puedes reprogramar a una hora pasada."}, status=status.HTTP_400_BAD_REQUEST)

    servicio = cita.servicio
    dentista = cita.dentista
    duracion = servicio.duracion_estimada or 30
    fin_dt = datetime.combine(nueva_fecha, nueva_hora) + timedelta(minutes=duracion)

    slots_libres = set(
        obtener_slots_disponibles(
            dentista,
            nueva_fecha,
            servicio,
            minutos_bloque=15,
        )
    )
    slot_key = nueva_hora.strftime("%H:%M")
    if slot_key not in slots_libres:
        return Response({"detail": "Ese horario ya no está disponible."}, status=status.HTTP_409_CONFLICT)

    cita.fecha = nueva_fecha
    cita.hora_inicio = nueva_hora
    cita.hora_fin = fin_dt.time()
    cita.estado = "PENDIENTE"
    cita.veces_reprogramada = (cita.veces_reprogramada or 0) + 1
    cita.save(update_fields=["fecha", "hora_inicio", "hora_fin", "estado", "veces_reprogramada"])

    try:
        enviar_correo_confirmacion_cita(cita)
    except Exception as exc:
        print(f"[WARN] No se pudo enviar correo de reprogramación: {exc}")

    try:
        crear_aviso_por_cita(cita, "REPROGRAMADA", "Cita reprogramada desde la app móvil.")
    except Exception as exc:
        print(f"[WARN] No se pudo crear aviso reprogramación: {exc}")

    return Response(
        {
            "id": cita.id,
            "servicio": {"id": servicio.id, "nombre": servicio.nombre},
            "fecha": cita.fecha.isoformat(),
            "hora": slot_key,
            "estado": cita.estado,
            "dentista": {"id": dentista.id, "nombre": dentista.nombre},
        }
    )
