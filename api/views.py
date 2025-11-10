# api/views.py
from rest_framework import generics
from domain.models import Servicio
from .serializers import ServicioSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .chatbot_logic import obtener_respuesta_bot 

class ServicioListAPIView(generics.ListAPIView):
    serializer_class = ServicioSerializer
    queryset = Servicio.objects.filter(activo=True).order_by("nombre")


@csrf_exempt # Exención temporal para facilitar pruebas rápidas desde JS
@require_POST
def chatbot_api(request):
    """API que recibe mensajes del chat y devuelve respuestas."""
    try:
        data = json.loads(request.body)
        mensaje = data.get('mensaje', '')
        
        if not mensaje:
            return JsonResponse({'respuesta': '🤔 No escribiste nada.'})

        respuesta = obtener_respuesta_bot(mensaje)
        return JsonResponse({'respuesta': respuesta})

    except json.JSONDecodeError:
        return JsonResponse({'respuesta': 'Error de comunicación.'}, status=400)