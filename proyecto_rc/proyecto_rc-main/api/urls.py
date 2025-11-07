# api/urls.py
from django.urls import path
from .views import ServicioListAPIView

app_name = "api"

urlpatterns = [
    path("servicios/", ServicioListAPIView.as_view(), name="servicio-list"),
]
