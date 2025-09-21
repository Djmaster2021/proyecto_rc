from django.urls import path
from . import views

# app_name es OBLIGATORIO para que {% url 'dentista:...' %} funcione.
# Le dice a Django que estas URLs pertenecen al grupo "dentista".
app_name = 'dentista'

urlpatterns = [
    # Cada path conecta una URL, una vista de views.py y un nombre único.
    
    # URL: /dentista/ -> Vista: views.dashboard -> Nombre: 'dashboard'
    path('', views.dashboard, name='dashboard'),
    
    # URL: /dentista/agenda/ -> Vista: views.agenda -> Nombre: 'agenda'
    path('agenda/', views.agenda, name='agenda'),
    
    # URL: /dentista/pacientes/ -> Vista: views.pacientes -> Nombre: 'pacientes'
    path('pacientes/', views.pacientes, name='pacientes'),
    
    # URL: /dentista/pagos/ -> Vista: views.pagos -> Nombre: 'pagos'
    path('pagos/', views.pagos, name='pagos'),
    
    # URL: /dentista/servicios/ -> Vista: views.servicios -> Nombre: 'servicios'
    path('servicios/', views.servicios, name='servicios'),
    
    # URL: /dentista/reportes/ -> Vista: views.reportes -> Nombre: 'reportes'
    path('reportes/', views.reportes, name='reportes'),

    # URL: /dentista/historial/ -> Vista: views.historial -> Nombre: 'historial'
    path('historial/', views.historial, name='historial'),

    # URL: /dentista/vista-paciente/ -> Vista: views.vista_paciente -> Nombre: 'vista-paciente'
    path('vista-paciente/', views.vista_paciente, name='vista_paciente'),
]

