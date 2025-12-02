# ============================================================
#  URLS DEL MÓDULO DENTISTA — RC DENTAL PRO
# ============================================================

from django.urls import path
from . import views

app_name = "dentista"

urlpatterns = [
    # Dashboard principal
    path("dashboard/", views.dashboard_dentista, name="dashboard"),

    # Agenda (usa templates/dentista/agenda.html)
    path("agenda/", views.agenda_dentista, name="agenda"),
    path("agenda/<str:modo>/", views.agenda_dentista, name="agenda_modo"),
    path('api/get-slots/', views.obtener_slots_disponibles, name='get_slots'),

    # Citas
    path("cita/crear/", views.crear_cita_manual, name="crear_cita_manual"),
    path("cita/eliminar/<int:id>/", views.eliminar_cita, name="eliminar_cita"),

    # Consulta / expediente (usa templates/dentista/consulta.html)
    path("consulta/<int:id>/", views.consulta, name="consulta"),

    # 👇 Alias para compatibilidad con templates que usan 'vista_consulta'
    #    Ej: {% url 'dentista:vista_consulta' cita.id %}
    path("consulta/vista/<int:id>/", views.consulta, name="vista_consulta"),

    # Pacientes del dentista
    path("pacientes/", views.pacientes, name="pacientes"),
    path("pacientes/registrar/", views.registrar_paciente, name="registrar_paciente"),
    path("pacientes/<int:id>/editar/", views.editar_paciente, name="editar_paciente"),
    path("pacientes/eliminar/<int:id>/", views.eliminar_paciente, name="eliminar_paciente"),
    path("paciente/<int:id>/", views.detalle_paciente, name="detalle_paciente"),

    # Pagos del dentista
    path("pagos/", views.pagos, name="pagos"),

    # Reportes (base)
    path("reportes/", views.reportes, name="reportes"),

    # Servicios del dentista
    path("servicios/", views.servicios, name="servicios"),

    # Penalizaciones / pagos pendientes
    path("penalizaciones/", views.penalizaciones, name="penalizaciones"),

    # Configuración del dentista
    path("configuracion/", views.configuracion, name="configuracion"),

    # Soporte / ayuda
    path("soporte/", views.soporte, name="soporte"),
]
