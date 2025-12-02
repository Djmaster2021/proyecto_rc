from django.urls import path
from . import views

urlpatterns = [
    # API para obtener lista de servicios (opcional)
    path('servicios/', views.ServicioListAPIView.as_view(), name='api_servicios'),

    # API para el Chatbot
    path('chatbot/', views.chatbot_api, name='chatbot_api'),

    # API PRINCIPAL DE HORARIOS
    # Esta es la que usa el calendario para saber qué horas están libres
    path('slots/', views.api_slots_disponibles, name='api_slots'),
]