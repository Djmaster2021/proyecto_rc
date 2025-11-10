from django.urls import path
from . import views

app_name = "paciente"

urlpatterns = [
    # --- VISTAS PRINCIPALES ---
    path("", views.dashboard, name="dashboard"),
    path("citas/", views.citas, name="citas"),
    path("pagos/", views.pagos, name="pagos"),

    # --- MOTOR DE AGENDAMIENTO ---
    path("api/horarios/", views.api_horarios_disponibles, name="api_horarios"),
    path("agendar/crear/", views.agendar_cita, name="agendar_crear"),

    # --- FLUJO DE PAGOS (MERCADOPAGO) --- <--- ¡ESTO ES LO NUEVO!
    path("pago/iniciar/<int:cita_id>/", views.iniciar_pago, name="iniciar_pago"),
    path("pago/exito/", views.pago_exitoso, name="pago_exitoso"),
    path("pago/fallo/", views.pago_fallido, name="pago_fallido"),
    path("pago/pendiente/", views.pago_pendiente, name="pago_pendiente"),

    # --- ACCIONES DE CITAS (PLACEHOLDERS) ---
    path("reprogramar/<int:cita_id>/", views.reprogramar_placeholder, name="reprogramar"),
    path("cancelar/<int:cita_id>/", views.cancelar_placeholder, name="cancelar"),
    path("confirmar-cita/<str:token>/", views.confirmar_por_email, name="confirmar_por_email"),
    path("cita/<int:cita_id>/encuesta/", views.encuesta_satisfaccion, name="encuesta_satisfaccion"),
]