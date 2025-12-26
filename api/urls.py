from django.urls import path
from . import views

urlpatterns = [
    # Healthcheck (sin auth)
    path('health/', views.health_check, name='api_health'),

    # API para obtener lista de servicios (opcional)
    path('servicios/', views.ServicioListAPIView.as_view(), name='api_servicios'),

    # API para el Chatbot
    path('chatbot/', views.chatbot_api, name='chatbot_api'),

    # API PRINCIPAL DE HORARIOS
    # Esta es la que usa el calendario para saber qué horas están libres
    path('slots/', views.api_slots_disponibles, name='api_slots'),

    # API para crear citas desde móvil
    path('citas/', views.api_crear_cita, name='api_crear_cita'),

    # Listar, cancelar, reprogramar
    path('citas/listar/', views.api_listar_citas, name='api_listar_citas'),
    path('citas/<int:cita_id>/cancelar/', views.api_cancelar_cita, name='api_cancelar_cita'),
    path('citas/<int:cita_id>/reprogramar/', views.api_reprogramar_cita, name='api_reprogramar_cita'),
]
