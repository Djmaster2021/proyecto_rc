import logging
import time
from urllib.parse import urljoin

import mercadopago
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

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

    logger.info("Creando preferencia MercadoPago para cita %s (sandbox=%s)", cita.id, is_test_token)

    # 1. Configurar SDK
    sdk = mercadopago.SDK(token)

    # 2. URLs de retorno
    base_url = (getattr(settings, "SITE_BASE_URL", "") or request.build_absolute_uri("/")).rstrip("/")
    # Construimos back_urls explícitas para evitar hosts "testserver"
    back_url_success = f"{base_url}{reverse('paciente:pago_exitoso')}"
    back_url_failure = f"{base_url}{reverse('paciente:pago_fallido')}"
    back_url_pending = f"{base_url}{reverse('paciente:pago_pendiente')}"

    # 3. Datos de la Preferencia
    payer_name = cita.paciente.user.first_name or "Test"
    payer_lastname = cita.paciente.user.last_name or "User"
    # Para sandbox usa DNI/12345678 (recomendado por MP para tarjetas APRO)
    payer_id_type = "DNI"
    payer_id_number = "12345678"

    # Webhook sin querystring: usamos secreto por ruta cuando está configurado.
    secret = getattr(settings, "MERCADOPAGO_WEBHOOK_SECRET", "")
    if secret:
        webhook_path = reverse("paciente:mp_webhook_key", args=[secret])
    else:
        webhook_path = reverse("paciente:mp_webhook")
    webhook_url = request.build_absolute_uri(webhook_path)

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
        "external_reference": str(cita.id),
        "statement_descriptor": "DENTAL RC",
    }

    preference_data["back_urls"] = {
        "success": back_url_success,
        "failure": back_url_failure,
        "pending": back_url_pending,
    }
    preference_data["auto_return"] = "approved"

    # Para desarrollo local (localhost/127.0.0.1), MercadoPago puede rechazar notification_url/auto_return.
    is_local = any(h in base_url for h in ("127.0.0.1", "localhost"))
    if not is_local:
        preference_data["notification_url"] = webhook_url
    else:
        logger.info("Entorno local detectado, omitiendo notification_url.")
        preference_data.pop("auto_return", None)

    # Log de diagnóstico en nivel debug (evita exponer detalles en stdout por defecto)
    logger.debug("MP back_urls usadas: %s", preference_data["back_urls"])
    logger.debug("MP notification_url: %s", preference_data.get("notification_url"))
    logger.debug("MP SITE_BASE_URL: %s", getattr(settings, "SITE_BASE_URL", ""))
    logger.info(
        "Creando preferencia MP cita=%s back_urls=%s",
        cita.id,
        preference_data["back_urls"],
    )

    # 4. Crear la preferencia (con reintento si falla auto_return)
    preference_response = sdk.preference().create(preference_data)
    logger.debug("Respuesta de MercadoPago status=%s", preference_response.get("status"))

    if preference_response["status"] != 201:
        # Si MP rechaza auto_return/back_urls, reintenta sin auto_return
        error_msg = str(preference_response.get("response", ""))
        if "auto_return invalid" in error_msg or "back_url" in error_msg:
            fallback_data = dict(preference_data)
            fallback_data.pop("auto_return", None)
            fallback_data.pop("notification_url", None)
            logger.warning("Reintentando preferencia sin auto_return por error MP: %s", error_msg)
            preference_response = sdk.preference().create(fallback_data)
        else:
            raise Exception(f"MP Error {preference_response['status']}: {preference_response.get('response', 'Sin detalle')}")

    # 5. Validar respuesta final
    if preference_response["status"] == 201:
        return preference_response["response"].get("sandbox_init_point") or preference_response["response"].get("init_point")
    raise Exception(f"MP Error {preference_response['status']}: {preference_response.get('response', 'Sin detalle')}")
