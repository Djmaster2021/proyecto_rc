from unittest.mock import patch

from django.test import TestCase, override_settings, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User

from domain.models import Dentista, Paciente, Cita, Pago, Servicio
from paciente.mp_service import crear_preferencia_pago


@override_settings(MERCADOPAGO_WEBHOOK_SECRET="testsecret", MERCADOPAGO_ACCESS_TOKEN="tokentest", DEBUG=False)
class PagoMercadoPagoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pac3", password="pwd")
        self.dentista = Dentista.objects.create(user=User.objects.create_user(username="doc3", password="pwd3"), nombre="Dr Pago")
        self.paciente = Paciente.objects.create(user=self.user, dentista=self.dentista, nombre="Paciente MP")
        self.servicio = Servicio.objects.create(dentista=self.dentista, nombre="Limpieza", precio=500, duracion_estimada=30)
        self.cita = Cita.objects.create(
            dentista=self.dentista,
            paciente=self.paciente,
            servicio=self.servicio,
            fecha="2025-01-01",
            hora_inicio="09:00",
            hora_fin="09:30",
            estado="PENDIENTE",
        )
        self.pago = Pago.objects.create(cita=self.cita, monto=500, estado="PENDIENTE", metodo="EFECTIVO")
        self.factory = RequestFactory()

    @patch("paciente.views.crear_preferencia_pago", return_value="http://mp.test/checkout")
    def test_iniciar_pago_redirige_a_mercadopago(self, mock_pref):
        self.client.login(username="pac3", password="pwd")
        url = reverse("paciente:iniciar_pago", args=[self.cita.id])
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 302)
        self.assertIn("mp.test/checkout", resp["Location"])
        mock_pref.assert_called_once()

        # El método debe marcarse como MercadoPago al salir al checkout
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.metodo, "MERCADOPAGO")

    @patch("paciente.views.mercadopago.SDK")
    def test_webhook_actualiza_pago_aprobado(self, mock_sdk):
        # Simular respuesta MP aprobada
        mock_payment = mock_sdk.return_value.payment.return_value
        mock_payment.get.return_value = {
            "status": 200,
            "response": {
                "status": "approved",
                "external_reference": str(self.cita.id),
                "transaction_amount": float(self.pago.monto),
            },
        }

        url = reverse("paciente:mp_webhook")
        payload = {"data": {"id": "321"}}
        resp = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="testsecret",
        )

        self.assertEqual(resp.status_code, 200)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.estado, "COMPLETADO")
        self.assertEqual(self.pago.metodo, "MERCADOPAGO")

    @patch("paciente.views.mercadopago.SDK")
    def test_webhook_rechaza_monto_inconsistente(self, mock_sdk):
        mock_payment = mock_sdk.return_value.payment.return_value
        mock_payment.get.return_value = {
            "status": 200,
            "response": {
                "status": "approved",
                "external_reference": str(self.cita.id),
                "transaction_amount": float(self.pago.monto) + 1,
            },
        }

        url = reverse("paciente:mp_webhook")
        payload = {"data": {"id": "999"}}
        resp = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="testsecret",
        )

        self.assertEqual(resp.status_code, 400)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.estado, "PENDIENTE")

    def test_webhook_sin_secreto_es_rechazado(self):
        url = reverse("paciente:mp_webhook")
        payload = {"data": {"id": "999"}}
        resp = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(resp.status_code, 403)

    @patch("paciente.views.mercadopago.SDK")
    def test_webhook_acepta_secreto_en_ruta(self, mock_sdk):
        mock_payment = mock_sdk.return_value.payment.return_value
        mock_payment.get.return_value = {
            "status": 200,
            "response": {
                "status": "approved",
                "external_reference": str(self.cita.id),
                "transaction_amount": float(self.pago.monto),
            },
        }
        url = reverse("paciente:mp_webhook_key", args=["testsecret"])
        payload = {"data": {"id": "123"}}
        resp = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(resp.status_code, 200)

    @override_settings(WEBHOOK_MAX_BODY_BYTES=32)
    def test_webhook_payload_excesivo_rechazado(self):
        url = reverse("paciente:mp_webhook")
        payload = {"data": {"id": "x" * 500}}
        resp = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="testsecret",
        )
        self.assertEqual(resp.status_code, 413)

    @patch("paciente.mp_service.mercadopago.SDK")
    @override_settings(
        MERCADOPAGO_WEBHOOK_SECRET="testsecret",
        SITE_BASE_URL="https://app.example.com",
        ALLOWED_HOSTS=["testserver", "127.0.0.1", "app.example.com"],
    )
    def test_preferencia_no_filtra_secreto_en_notification_url(self, mock_sdk):
        mock_sdk.return_value.preference.return_value.create.return_value = {
            "status": 201,
            "response": {"init_point": "https://mp.test/init", "sandbox_init_point": "https://mp.test/sandbox"},
        }
        req = self.factory.post("/dummy")
        req.META["HTTP_HOST"] = "app.example.com"
        req.META["wsgi.url_scheme"] = "https"

        crear_preferencia_pago(self.cita, req)

        call_data = mock_sdk.return_value.preference.return_value.create.call_args[0][0]
        self.assertIn("notification_url", call_data)
        self.assertNotIn("secret=", call_data["notification_url"])
        self.assertIn("/paciente/pagos/webhook/testsecret/", call_data["notification_url"])
