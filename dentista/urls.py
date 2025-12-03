from django.urls import path
from . import views

app_name = "dentista"

urlpatterns = [
    # ==========================
    # DASHBOARD
    # ==========================
    path("dashboard/", views.dashboard_dentista, name="dashboard"),
    path("agenda/semana/", views.agenda_modo, {"modo": "semana"}, name="agenda_semana"),
    # ==========================
    # AGENDA Y CITAS
    # ==========================
    path("agenda/", views.agenda_dentista, name="agenda"),
    path("agenda/modo/<str:modo>/", views.agenda_modo, name="agenda_modo"),
    path("agenda/crear/", views.crear_cita_manual, name="crear_cita_manual"),
    path("citas/<int:id>/eliminar/", views.eliminar_cita, name="eliminar_cita"),
    
    # API para obtener horas libres (AJAX)
    path("api/slots/", views.obtener_slots_disponibles, name="obtener_slots"),

    # ==========================
    # CONSULTA MÉDICA
    # ==========================
    path("consulta/<int:id>/", views.consulta, name="consulta"),

    # ==========================
    # SERVICIOS (CRUD)
    # ==========================
    # Nota: Ya no existe "nuevo", todo se hace en la misma página con Modals
    path("servicios/", views.servicios, name="servicios"),
    path("servicios/crear/", views.servicio_crear, name="servicio_crear"),
    path("servicios/<int:id>/editar/", views.servicio_editar, name="servicio_editar"),
    path("servicios/<int:id>/toggle/", views.servicio_toggle_estado, name="servicio_toggle"),
    path("servicios/<int:id>/eliminar/", views.servicio_eliminar, name="servicio_eliminar"),

    # ==========================
    # PACIENTES
    # ==========================
    path("pacientes/", views.pacientes, name="pacientes"),
    path("pacientes/nuevo/", views.registrar_paciente, name="registrar_paciente"),
    path("pacientes/<int:id>/", views.detalle_paciente, name="detalle_paciente"),
    path("pacientes/<int:id>/editar/", views.editar_paciente, name="editar_paciente"),
    path("pacientes/<int:id>/eliminar/", views.eliminar_paciente, name="eliminar_paciente"),

    # Odontograma (APIs)
    path("pacientes/<int:id>/odontograma/data/", views.odontograma_data, name="odontograma_data"),
    path("pacientes/<int:id>/odontograma/guardar/", views.odontograma_guardar, name="odontograma_guardar"),

    # ==========================
    # FINANZAS (PAGOS)
    # ==========================
    path("pagos/", views.pagos, name="pagos"),
    path("pagos/registrar/", views.registrar_pago, name="registrar_pago"),

    # ==========================
    # CONFIGURACIÓN Y SOPORTE
    # ==========================
    path("configuracion/", views.configuracion, name="configuracion"),
    path("configuracion/horario/<int:id>/eliminar/", views.eliminar_horario, name="eliminar_horario"),
    path("soporte/", views.soporte, name="soporte"),
    path("penalizaciones/", views.penalizaciones, name="penalizaciones"),

    # ==========================
    # REPORTES
    # ==========================
    path("reportes/", views.reportes, name="reportes"),
    path("reportes/csv/", views.reporte_csv, name="reporte_csv"),
    path("reportes/pdf/", views.reporte_pdf, name="reporte_pdf"),
]
