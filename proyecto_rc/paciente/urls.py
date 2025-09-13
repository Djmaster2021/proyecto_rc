# proyecto_rc/urls.py
from django.contrib import admin
from django.urls import path, include
from paciente import views as paciente_views 

urlpatterns = [
    path("admin/", admin.site.urls),
    path("paciente/", include(("paciente.urls", "paciente"), namespace="paciente")),

    # Alias global para compatibilidad con templates que llamen {% url 'agendar' %}
    path("paciente/agendar/", paciente_views.agendar_placeholder, name="agendar"),
]
