# api/urls.py
from django.urls import path
from .views import ServicioListAPIView
from. import views

app_name = "api"

urlpatterns = [
    path("servicios/", ServicioListAPIView.as_view(), name="servicio-list"),
    path('chatbot/', views.chatbot_api, name='chatbot_api'),
    path("slots-disponibles/",views.api_slots_disponibles,name="slots_disponibles",
    ),
]