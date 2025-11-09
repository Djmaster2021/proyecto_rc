from django.urls import path
from . import views

app_name = "dentista"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    
    # Gestión Clínica
    path("agenda/", views.agenda, name="agenda"),
    path("pacientes/", views.pacientes, name="pacientes"),
    path("pacientes/<int:paciente_id>/", views.detalle_paciente, name="detalle_paciente"),

    # Acciones de Citas (INCLUYENDO la que faltaba)
    path("citas/<int:cita_id>/confirmar/", views.confirmar_cita, name="confirmar_cita"),
    path("citas/<int:cita_id>/consulta/", views.vista_consulta, name="vista_consulta"),
    path("citas/<int:cita_id>/no-show/", views.marcar_no_show, name="marcar_no_show"),
    # Agregamos esta ruta de compatibilidad para que no falle si un HTML viejo la llama
    path("citas/<int:cita_id>/completar/", views.completar_cita, name="completar_cita"),

    # Gestión Administrativa
    path("pagos/", views.pagos, name="pagos"),
    path("servicios/", views.gestionar_servicios, name="servicios"),
    path("penalizaciones/", views.penalizaciones, name="penalizaciones"),
    
    # Otros
    path("reportes/", views.reportes_placeholder, name="reportes"),
    path("configuracion/", views.configuracion, name="configuracion"),
    path("configuracion/eliminar/<int:horario_id>/", views.eliminar_horario, name="eliminar_horario"),
    path("soporte/", views.soporte_placeholder, name="soporte"),
]