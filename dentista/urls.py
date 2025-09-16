# dentista/urls.py
from django.urls import path
from . import views

app_name = "dentista"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("agenda/", views.agenda, name="agenda"),
    path("pacientes/", views.pacientes, name="pacientes"),
    path("pagos/", views.pagos, name="pagos"),
]
