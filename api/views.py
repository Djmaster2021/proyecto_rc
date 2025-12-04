import json
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods
from rest_framework import generics, permissions, serializers

# IMPORTANTE: Importamos los modelos correctos desde 'domain'
# Agregamos 'Dentista' para poder buscarlo por ID
from domain.models import Servicio, Horario, Dentista

# Chatbot IA / fallback
try:
    from domain.ai_chatbot import responder_chatbot
except Exception:
    responder_chatbot = None
from domain.ai_services import obtener_slots_disponibles


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
    provided_secret = request.headers.get("X-CHATBOT-SECRET") or request.GET.get("secret")
    same_origin = False
    try:
        referer = request.META.get("HTTP_REFERER", "")
        proto = "https" if request.is_secure() else "http"
        host = request.get_host()
        same_origin = referer.startswith(f"{proto}://{host}")
    except Exception:
        same_origin = False

    if expected_secret:
        if provided_secret == expected_secret:
            pass  # OK, secret válido
        elif same_origin:
            # Permitimos llamadas desde el mismo origen aunque no manden el header (chat embebido)
            pass
        else:
            print(f"[CHATBOT] Forbidden secret from IP {ip}")
            return JsonResponse({"message": "Forbidden"}, status=403)

    # Freno simple por IP para evitar abuso.
    key = f"chatbot:rate:{ip}"
    hits = cache.get(key, 0)
    max_hits = 20  # más conservador
    if hits >= max_hits:
        print(f"[CHATBOT] Throttle IP {ip} ({hits} req/min)")
        return JsonResponse({"message": "⏳ Demasiadas peticiones, espera un minuto."}, status=429)
    cache.set(key, hits + 1, timeout=60)

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
                return JsonResponse({"message": "🤔 No escribiste nada."}, status=400)

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
        return JsonResponse({"message": "❌ Error de conexión."}, status=500)


# ---------------------------------------------------------
# Slots disponibles para una fecha / servicio
# ---------------------------------------------------------
@login_required
@require_GET
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
        try:
            dentista = request.user.dentista 
        except AttributeError:
            dentista = None

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
