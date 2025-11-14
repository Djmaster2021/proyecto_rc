# api/views.py
from rest_framework import generics
from domain.models import Servicio
# from .serializers import ServicioSerializer # Asumo que tienes un serializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .chatbot_logic import obtener_respuesta_bot 

# Ejemplo de serializer para evitar errores
class ServicioSerializer: pass

class ServicioListAPIView(generics.ListAPIView):
    # serializer_class = ServicioSerializer
    queryset = Servicio.objects.filter(activo=True).order_by("nombre")


@csrf_exempt
@require_POST
def chatbot_api(request):
    """API que recibe mensajes del chat y devuelve respuestas."""
    try:
        data = json.loads(request.body)
        # FIX 1: LEER 'query' (formato estándar JS)
        mensaje = data.get('query', '') 
        
        if not mensaje:
            return JsonResponse({'message': '🤔 No escribiste nada.'})

        respuesta = obtener_respuesta_bot(mensaje)
        # FIX 2: DEVOLVER 'message' (formato esperado por el frontend)
        return JsonResponse({'message': respuesta}) 

    except json.JSONDecodeError:
        return JsonResponse({'message': 'Error de formato.'}, status=400)
    except Exception as e:
        # Esto capturará cualquier error interno en la lógica
        print(f"Error en chatbot: {e}")
        return JsonResponse({'message': '❌ Error de conexión.'}, status=500)