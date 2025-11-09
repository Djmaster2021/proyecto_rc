from django.urls import path
from . import views

app_name = "dentista"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    
    # --- GESTIÓN CLÍNICA ---
    path("agenda/", views.agenda, name="agenda"),
    
    # Pacientes y su Historial
    path("pacientes/", views.pacientes, name="pacientes"),
    path("pacientes/<int:paciente_id>/", views.detalle_paciente, name="detalle_paciente"), # <--- NUEVA RUTA

    # Acciones de Citas
    path("citas/<int:cita_id>/confirmar/", views.confirmar_cita, name="confirmar_cita"),
    path("citas/<int:cita_id>/consulta/", views.vista_consulta, name="vista_consulta"),
    # ...
    # --- GESTIÓN ADMINISTRATIVA (Placeholders) ---
    path("pagos/", views.pagos_placeholder, name="pagos"),
    path("servicios/", views.servicios_placeholder, name="servicios"),
    path("penalizaciones/", views.penalizaciones_placeholder, name="penalizaciones"),
    path("reportes/", views.reportes_placeholder, name="reportes"),
    path("configuracion/", views.configuracion_placeholder, name="configuracion"),
    path("soporte/", views.soporte_placeholder, name="soporte"),
]