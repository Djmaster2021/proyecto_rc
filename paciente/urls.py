from django.urls import path
from . import views

app_name = 'paciente'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('api/slots/', views.api_slots, name='api_slots'),

    # Perfil
    path('completar-perfil/', views.completar_perfil_paciente, name='completar_perfil'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('cancelar-registro/', views.cancelar_registro_paciente, name='cancelar_registro'),
    path('citas/<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    path('citas/reprogramar/<int:cita_id>/', views.reprogramar_cita, name='reprogramar_cita'),
    path('pagos/<int:cita_id>/', views.iniciar_pago, name='iniciar_pago'),
    path('pagos/exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('pagos/fallido/', views.pago_fallido, name='pago_fallido'),
    path('pagos/pendiente/', views.pago_pendiente, name='pago_pendiente'),
    path('pagos/webhook/', views.mp_webhook, name='mp_webhook'),
    path('confirmar/<str:token>/', views.confirmar_por_email, name='confirmar_por_email'),
    path('recibo/<int:pago_id>/', views.recibo_pago_pdf, name='recibo_pago_pdf'),
    path('citas/<int:cita_id>/feedback/', views.feedback_cita, name='feedback_cita'),

    # Funciones
    path('agendar/', views.agendar_cita, name='agendar_cita'),
    path('mis-pagos/', views.mis_pagos, name='mis_pagos'),
    path('pagar-penalizacion/', views.pagar_penalizacion, name='pagar_penalizacion'),
    path('contactar-dentista/', views.contactar_dentista, name='contactar_dentista'),
]
