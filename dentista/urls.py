from django.urls import path
from . import views

app_name = 'dentista'

urlpatterns = [
    # --- DASHBOARD ---
    path('', views.dashboard, name='dashboard'),
    
    # --- AGENDA Y CITAS ---
    path('agenda/', views.agenda, name='agenda'),
    path('citas/crear-manual/', views.crear_cita_manual, name='crear_cita_manual'),
    path('citas/<int:cita_id>/confirmar/', views.confirmar_cita, name='confirmar_cita'),
    path('citas/<int:cita_id>/eliminar/', views.eliminar_cita, name='eliminar_cita'),
    path('citas/<int:cita_id>/no-show/', views.marcar_no_show, name='marcar_no_show'),
    path('citas/<int:cita_id>/consulta/', views.vista_consulta, name='vista_consulta'),
    path('citas/<int:cita_id>/completar/', views.completar_cita, name='completar_cita'),
    path('citas/<int:cita_id>/actualizar-nota/', views.actualizar_nota_cita, name='actualizar_nota_cita'),
    
    # --- PACIENTES ---
    path('pacientes/', views.pacientes, name='pacientes'),
    path('pacientes/<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('pacientes/<int:paciente_id>/editar/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/<int:paciente_id>/eliminar/', views.eliminar_paciente, name='eliminar_paciente'),

    # --- SERVICIOS (CATÁLOGO) ---
    path('servicios/', views.gestionar_servicios, name='servicios'),
    path('servicios/eliminar/<int:servicio_id>/', views.eliminar_servicio, name='eliminar_servicio'),

    # --- FINANZAS Y PAGOS ---
    path('pagos/', views.pagos, name='pagos'),
    path('pagos/registrar/', views.registrar_pago_efectivo, name='registrar_pago_efectivo'),
    # BORRADA LA LÍNEA 'api/grafica/' QUE CAUSABA EL ERROR

    # --- REPORTES ---
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/csv/', views.exportar_citas_csv, name='exportar_citas_csv'),
    path('reportes/pdf/', views.exportar_citas_pdf, name='exportar_citas_pdf'),

    # --- CONFIGURACIÓN Y OTROS ---
    path('penalizaciones/', views.penalizaciones, name='penalizaciones'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('configuracion/horario/<int:horario_id>/eliminar/', views.eliminar_horario, name='eliminar_horario'),
    path('soporte/', views.soporte, name='soporte'),
]