# api/urls.py
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = "api"

urlpatterns = [
    # Punto de entrada de la API (ajusta si usas DRF routers)
    path("", getattr(views, "api_root", TemplateView.as_view(template_name="api/index.html")), name="root"),
    # Si tienes endpoints adicionales en views.py: se usarán automáticamente si existen
    # Ejemplo: path("pacientes/", getattr(views,"pacientes_list", ...), name="pacientes-list")
]
