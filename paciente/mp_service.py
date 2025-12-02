import mercadopago
from django.conf import settings
from django.urls import reverse
import time

def crear_preferencia_pago(cita, request):
    # --- MODO DETECTIVE ACTIVADO ---
    token = settings.MERCADOPAGO_ACCESS_TOKEN
    print(f"\n🔑 LLAVE ACTUAL EN MEMORIA: {token[:15]}...\n") 
    
    # Generamos un email único basado en la hora actual
    email_unico = f"paciente_{int(time.time())}@test.com"

    # 1. Configurar SDK
    sdk = mercadopago.SDK(token)

    # 2. URLs de retorno
    back_url_success = request.build_absolute_uri(reverse('paciente:pago_exitoso'))
    back_url_failure = request.build_absolute_uri(reverse('paciente:pago_fallido'))
    back_url_pending = request.build_absolute_uri(reverse('paciente:pago_pendiente'))

    # 3. Datos de la Preferencia
    preference_data = {
        "items": [
            {
                "id": str(cita.servicio.id),
                "title": f"Tratamiento: {cita.servicio.nombre}",
                "quantity": 1,
                "currency_id": "MXN",
                "unit_price": float(cita.servicio.precio)
            }
        ],
        "payer": {
            "name": cita.paciente.user.first_name or "Paciente",
            "surname": cita.paciente.user.last_name or "Prueba",
            "email": email_unico,
        },
        "back_urls": {
            "success": back_url_success,
            "failure": back_url_failure,
            "pending": back_url_pending
        }, 
        # "auto_return": "approved",
        "external_reference": str(cita.id),
        "statement_descriptor": "DENTAL RC",
    }

    # 4. Crear la preferencia
    print(f"🔵 Enviando datos a MP con email único: {email_unico}")
    preference_response = sdk.preference().create(preference_data)
    print("🟡 Respuesta de MercadoPago:", preference_response)
    
    # 5. Validar respuesta
    if preference_response["status"] == 201:
        return preference_response["response"]["sandbox_init_point"]
    else:
        raise Exception(f"MP Error {preference_response['status']}: {preference_response.get('response', 'Sin detalle')}")
