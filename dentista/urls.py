# dentista/urls.py
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = "dentista"

urlpatterns = [
    path("", getattr(views, "dashboard", TemplateView.as_view(template_name="dentista/dashboard.html")), name="dashboard"),
    path("agenda/", getattr(views, "agenda", TemplateView.as_view(template_name="dentista/agenda.html")), name="agenda"),
    path("pacientes/", getattr(views, "pacientes", TemplateView.as_view(template_name="dentista/pacientes.html")), name="pacientes"),
    path("pagos/", getattr(views, "pagos", TemplateView.as_view(template_name="dentista/pagos.html")), name="pagos"),
    path("servicios/", getattr(views, "servicios", TemplateView.as_view(template_name="dentista/servicios.html")), name="servicios"),
    path("reportes/", getattr(views, "reportes", TemplateView.as_view(template_name="dentista/reportes.html")), name="reportes"),
    path("historial/", getattr(views, "historial", TemplateView.as_view(template_name="dentista/historial.html")), name="historial"),
    path("vista-paciente/", getattr(views, "vista_paciente", TemplateView.as_view(template_name="dentista/vista-paciente.html")), name="vista_paciente"),
    path("configuracion/", views.configuracion, name="configuracion"),
    path("soporte/", views.soporte, name="soporte"),
]
