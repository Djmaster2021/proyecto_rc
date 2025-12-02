from django.urls import path
from . import views

app_name = 'paciente'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Perfil
    path('completar-perfil/', views.completar_perfil_paciente, name='completar_perfil'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('cancelar-registro/', views.cancelar_registro_paciente, name='cancelar_registro'),

    # Funciones
    path('agendar/', views.agendar_cita, name='agendar_cita'),
    path('mis-pagos/', views.mis_pagos, name='mis_pagos'),
]