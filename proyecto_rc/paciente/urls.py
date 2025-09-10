from django.urls import path
from . import views

app_name = "paciente"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("citas/", views.citas, name="citas"),
    path("pagos/", views.pagos, name="pagos"),
]
