from django.urls import path
from . import views

app_name = "paciente"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # API horarios
    path("api/horarios/", views.api_horarios_disponibles, name="api_horarios"),

    # Citas
    path("citas/agendar/", views.agendar_cita, name="agendar_cita"),
    path("citas/<int:cita_id>/cancelar/", views.cancelar_cita, name="cancelar_cita"),
    path("citas/<int:cita_id>/reprogramar/", views.reprogramar_cita, name="reprogramar_cita"),
    
    # Confirmación
    path("confirmar-cita/<str:token>/", views.confirmar_por_email, name="confirmar_por_email"),

    # Perfil
    path("perfil/editar/", views.editar_perfil, name="editar_perfil"),

    # --- PAGOS (Bloque corregido) ---
    path("pago/<int:cita_id>/iniciar/", views.iniciar_pago, name="iniciar_pago"),
    path("pago/exitoso/", views.pago_exitoso, name="pago_exitoso"),
    path("pago/fallido/", views.pago_fallido, name="pago_fallido"),
    path("pago/pendiente/", views.pago_pendiente, name="pago_pendiente"),
    path("penalizacion/pagar/", views.pagar_penalizacion, name="pagar_penalizacion"),

    # Encuesta
    path("cita/<int:cita_id>/encuesta/", views.encuesta_satisfaccion, name="encuesta_satisfaccion"),
]