from django.urls import path
from . import views

app_name = 'dentista'

urlpatterns = [
    # DASHBOARD
    path('', views.dashboard, name='dashboard'),
    
    # AGENDA
    path('agenda/', views.agenda, name='agenda'),
    path('cita/crear/', views.crear_cita_manual, name='crear_cita_manual'),
    path('cita/<int:cita_id>/consulta/', views.vista_consulta, name='vista_consulta'),
    path('cita/<int:cita_id>/confirmar/', views.confirmar_cita, name='confirmar_cita'),
    path('cita/<int:cita_id>/eliminar/', views.eliminar_cita, name='eliminar_cita'),
    path("pacientes/<int:paciente_id>/editar/", views.editar_paciente, name="editar_paciente"),
    # PACIENTES
    path('pacientes/', views.pacientes, name='pacientes'),
    path('pacientes/<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('pacientes/<int:paciente_id>/editar/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/<int:paciente_id>/eliminar/', views.eliminar_paciente, name='eliminar_paciente'),

    # SERVICIOS
    path('servicios/', views.gestionar_servicios, name='servicios'),
    path('servicios/eliminar/<int:servicio_id>/', views.eliminar_servicio, name='eliminar_servicio'),
    # ESTA ES LA LÍNEA QUE FALTABA:

    # FINANZAS
    path('pagos/', views.pagos, name='pagos'),
    path('pagos/nuevo/', views.registrar_pago_efectivo, name='registrar_pago_efectivo'),

    # REPORTES
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/pdf/', views.exportar_citas_pdf, name='exportar_citas_pdf'),
    path('reportes/csv/', views.exportar_citas_csv, name='exportar_citas_csv'),
    
    # OTROS
    path('configuracion/', views.configuracion, name='configuracion'),
    path('configuracion/horario/<int:horario_id>/eliminar/', views.eliminar_horario, name='eliminar_horario'),
    path('soporte/', views.soporte, name='soporte'),
    path('penalizaciones/', views.penalizaciones, name='penalizaciones'),
]