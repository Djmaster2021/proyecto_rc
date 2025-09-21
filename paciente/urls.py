# paciente/urls.py
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = "paciente"

urlpatterns = [
    path("", getattr(views, "dashboard", TemplateView.as_view(template_name="paciente/dashboard.html")), name="dashboard"),
    path("citas/", getattr(views, "citas", TemplateView.as_view(template_name="paciente/citas.html")), name="citas"),
    path("pagos/", getattr(views, "pagos", TemplateView.as_view(template_name="paciente/pagos.html")), name="pagos"),
    path("agendar/", views.agendar_placeholder, name="agendar"),
    path("reprogramar/<int:cita_id>/", views.reprogramar_placeholder, name="reprogramar"),
    path("cancelar/<int:cita_id>/", views.cancelar_placeholder, name="cancelar"),
]