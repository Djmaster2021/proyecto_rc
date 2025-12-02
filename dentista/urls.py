# ============================================================
#  URLS DEL MÓDULO DENTISTA — CORREGIDO
# ============================================================
from django.urls import path
from . import views

app_name = "dentista"

urlpatterns = [
    # --- Dashboard y Agenda ---
    path("dashboard/", views.dashboard_dentista, name="dashboard"),
    path("agenda/", views.agenda_dentista, name="agenda"),
    path("agenda/<str:modo>/", views.agenda_dentista, name="agenda_modo"),
    path('api/get-slots/', views.obtener_slots_disponibles, name='get_slots'),

    # --- Citas ---
    path("cita/crear/", views.crear_cita_manual, name="crear_cita_manual"),
    path("cita/eliminar/<int:id>/", views.eliminar_cita, name="eliminar_cita"),
    path("consulta/<int:id>/", views.consulta, name="consulta"),
    path("consulta/vista/<int:id>/", views.consulta, name="vista_consulta"),

    # --- Pacientes ---
    path("pacientes/", views.pacientes, name="pacientes"),
    path("pacientes/registrar/", views.registrar_paciente, name="registrar_paciente"),
    path("pacientes/<int:id>/editar/", views.editar_paciente, name="editar_paciente"),
    path("pacientes/eliminar/<int:id>/", views.eliminar_paciente, name="eliminar_paciente"),
    path("paciente/<int:id>/", views.detalle_paciente, name="detalle_paciente"),

    # --- ODONTOGRAMA (ESTAS SON LAS QUE FALTABAN) ---
    path("paciente/<int:id>/odontograma/", views.odontograma_data, name="odontograma_data"),
    path("paciente/<int:id>/odontograma/guardar/", views.odontograma_guardar, name="odontograma_guardar"),

    # --- Finanzas y Otros ---
    path("pagos/", views.pagos, name="pagos"),
    path("reportes/", views.reportes, name="reportes"),
    path("servicios/", views.servicios, name="servicios"),
    path("penalizaciones/", views.penalizaciones, name="penalizaciones"),
    path("configuracion/", views.configuracion, name="configuracion"),
    path("soporte/", views.soporte, name="soporte"),
]