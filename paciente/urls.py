from django.urls import path
from . import views

app_name = "paciente"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("citas/", views.citas, name="citas"),
    path("agendar/", views.agendar_placeholder, name="agendar"),
    path("reprogramar/<int:cita_id>/", views.reprogramar_placeholder, name="reprogramar"),
    path("cancelar/<int:cita_id>/", views.cancelar_placeholder, name="cancelar"),
]