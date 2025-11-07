# api/views.py
from rest_framework import generics
from domain.models import Servicio
from .serializers import ServicioSerializer

class ServicioListAPIView(generics.ListAPIView):
    serializer_class = ServicioSerializer
    queryset = Servicio.objects.filter(activo=True).order_by("nombre")
