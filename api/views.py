import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from rest_framework import generics, permissions, serializers

# IMPORTANTE: Importamos los modelos correctos desde 'domain'
# Agregamos 'Dentista' para poder buscarlo por ID
from domain.models import Servicio, Horario, Dentista

# Asumimos que estos archivos existen en tu proyecto (si no, coméntalos temporalmente)
from .chatbot_logic import obtener_respuesta_bot
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
@require_POST
def chatbot_api(request):
    """
    API que recibe mensajes del chat y devuelve respuestas.
    Espera JSON: {"query": "texto del usuario"}
    Responde: {"message": "respuesta del bot"}
    """
    try:
        data = json.loads(request.body)
        mensaje = data.get("query", "").strip()

        if not mensaje:
            return JsonResponse({"message": "🤔 No escribiste nada."}, status=400)

        respuesta = obtener_respuesta_bot(mensaje)
        return JsonResponse({"message": respuesta})

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
        return JsonResponse({"slots": slots})
    except Exception as e:
        print(f"Error calculando slots: {e}")
        return JsonResponse({"slots": []})