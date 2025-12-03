import mercadopago
from django.conf import settings
from django.urls import reverse
import time

def crear_preferencia_pago(cita, request):
    token = settings.MERCADOPAGO_ACCESS_TOKEN
    if not token:
        raise ValueError("MERCADOPAGO_ACCESS_TOKEN no configurado")

    is_test_token = token.startswith("TEST-")
    # Si es test, usa un mail de comprador de prueba configurable para evitar políticas de MP
    payer_email = (settings.MERCADOPAGO_TEST_PAYER_EMAIL or "").strip()
    if not payer_email:
        # Fallback: usa email real del paciente o uno único de respaldo
        payer_email = (
            cita.paciente.user.email
            or f"paciente_{cita.paciente.id or int(time.time())}@example.com"
        )

    print(f"\n🔑 LLAVE ACTUAL EN MEMORIA: {token[:15]}...\n") 
    if is_test_token:
        print(f"🧪 Modo test MP activo. Email de pagador usado: {payer_email}")

    # 1. Configurar SDK
    sdk = mercadopago.SDK(token)

    # 2. URLs de retorno
    back_url_success = request.build_absolute_uri(reverse('paciente:pago_exitoso'))
    back_url_failure = request.build_absolute_uri(reverse('paciente:pago_fallido'))
    back_url_pending = request.build_absolute_uri(reverse('paciente:pago_pendiente'))

    # 3. Datos de la Preferencia
    payer_name = cita.paciente.user.first_name or "Test"
    payer_lastname = cita.paciente.user.last_name or "User"
    # Para sandbox usa DNI/12345678 (recomendado por MP para tarjetas APRO)
    payer_id_type = "DNI"
    payer_id_number = "12345678"

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
            "name": payer_name,
            "surname": payer_lastname,
            "email": payer_email,
            "identification": {
                "type": payer_id_type,
                "number": payer_id_number,
            },
            "address": {
                "zip_code": "11550",
                "street_name": "Av. Prueba",
                "street_number": 123,
            },
            "phone": {
                "area_code": "55",
                "number": "55555555",
            },
        },
        "binary_mode": True,
        "payment_methods": {
            "installments": 1,
            "default_installments": 1,
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
    print(f"🔵 Enviando datos a MP con email: {payer_email}")
    preference_response = sdk.preference().create(preference_data)
    print("🟡 Respuesta de MercadoPago:", preference_response)
    
    # 5. Validar respuesta
    if preference_response["status"] == 201:
        # En test, devuelve sandbox_init_point; en prod, init_point
        return preference_response["response"].get("sandbox_init_point") or preference_response["response"].get("init_point")
    else:
        raise Exception(f"MP Error {preference_response['status']}: {preference_response.get('response', 'Sin detalle')}")
