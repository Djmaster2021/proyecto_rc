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


def _png_bytes():
    import base64
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )


@override_settings(SECURE_SSL_REDIRECT=False)
class PanelPacienteTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone

        self.user = User.objects.create_user(username="pac_panel", password="pwd", email="p@test.com", first_name="Ana", last_name="Ruiz")
        self.dentista = Dentista.objects.create(
            user=User.objects.create_user(username="doc_panel", password="pwd"),
            nombre="Lopez", direccion="Av. Juárez 10, CDMX", telefono="5512345678",
        )
        self.paciente = Paciente.objects.create(user=self.user, dentista=self.dentista, nombre="Ana Ruiz")
        self.servicio = Servicio.objects.create(dentista=self.dentista, nombre="Limpieza", precio=500, duracion_estimada=30)
        hoy = timezone.localdate()
        self.futura = Cita.objects.create(
            dentista=self.dentista, paciente=self.paciente, servicio=self.servicio,
            fecha=hoy + timedelta(days=5), hora_inicio="10:00", hora_fin="10:30", estado="PENDIENTE",
        )
        self.pasada = Cita.objects.create(
            dentista=self.dentista, paciente=self.paciente, servicio=self.servicio,
            fecha=hoy - timedelta(days=5), hora_inicio="10:00", hora_fin="10:30", estado="COMPLETADA",
        )
        Pago.objects.create(cita=self.futura, monto=500, estado="PENDIENTE", metodo="MERCADOPAGO")
        Pago.objects.create(cita=self.pasada, monto=500, estado="COMPLETADO", metodo="EFECTIVO")
        self.client.force_login(self.user)

    def test_paginas_del_panel_cargan(self):
        for name in ["dashboard", "mis_citas", "agendar_cita", "perfil", "mis_pagos"]:
            resp = self.client.get(reverse(f"paciente:{name}"))
            self.assertEqual(resp.status_code, 200, name)
        resp = self.client.get(reverse("paciente:feedback_cita", args=[self.pasada.id]))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_muestra_proxima_cita_y_saldo(self):
        resp = self.client.get(reverse("paciente:dashboard"))
        self.assertEqual(resp.context["proxima_cita"], self.futura)
        self.assertEqual(resp.context["stats"]["saldo_pendiente"], 500)
        self.assertEqual(resp.context["stats"]["completadas"], 1)
        self.assertContains(resp, reverse("paciente:reprogramar_cita", args=[self.futura.id]))
        self.assertContains(resp, "google.com/maps")

    def test_mis_citas_separa_proximas_y_pasadas(self):
        resp = self.client.get(reverse("paciente:mis_citas"))
        self.assertEqual(list(resp.context["proximas"]), [self.futura])
        self.assertEqual(list(resp.context["pasadas"]), [self.pasada])

    def test_editar_perfil_guarda_datos_y_foto(self):
        import shutil, tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile

        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        foto = SimpleUploadedFile("foto.png", _png_bytes(), content_type="image/png")
        with override_settings(MEDIA_ROOT=media):
            resp = self.client.post(reverse("paciente:perfil"), {
                "nombre": "Ana Ruiz Pérez", "telefono": "5598765432", "direccion": "Calle 1",
                "fecha_nacimiento": "1990-05-01", "antecedentes": "Alergia a penicilina", "imagen": foto,
            })
        self.assertRedirects(resp, reverse("paciente:perfil"))
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.telefono, "5598765432")
        self.assertEqual(self.paciente.antecedentes, "Alergia a penicilina")
        self.assertTrue(self.paciente.imagen.name.startswith("pacientes/"))

    def test_editar_perfil_rechaza_telefono_invalido(self):
        self.client.post(reverse("paciente:perfil"), {"nombre": "Ana Ruiz", "telefono": "123"})
        self.paciente.refresh_from_db()
        self.assertIsNone(self.paciente.telefono)

    def test_cancelar_regresa_a_pagina_de_origen(self):
        destino = reverse("paciente:mis_citas")
        resp = self.client.post(reverse("paciente:cancelar_cita", args=[self.futura.id]), {"next": destino})
        self.assertRedirects(resp, destino)
        self.futura.refresh_from_db()
        self.assertEqual(self.futura.estado, "CANCELADA")

    def test_cancelar_ignora_next_externo(self):
        resp = self.client.post(reverse("paciente:cancelar_cita", args=[self.futura.id]), {"next": "https://evil.com/"})
        self.assertRedirects(resp, reverse("paciente:dashboard"))

    def test_pagar_penalizacion_por_post_no_marca_pagado(self):
        inasistencia = Cita.objects.create(
            dentista=self.dentista, paciente=self.paciente, servicio=self.servicio,
            fecha="2025-01-01", hora_inicio="09:00", hora_fin="09:30", estado="INASISTENCIA",
        )
        pago = Pago.objects.create(cita=inasistencia, monto=300, estado="PENDIENTE")
        with patch("paciente.views.calcular_penalizacion_paciente", return_value={"estado": "pending", "recargo": 300}):
            self.client.post(reverse("paciente:pagar_penalizacion"))
        pago.refresh_from_db()
        self.assertEqual(pago.estado, "PENDIENTE")

    def test_pago_directo_no_se_ofrece_al_paciente(self):
        interno = Servicio.objects.create(dentista=self.dentista, nombre="Pago Directo", precio=0, duracion_estimada=15)
        resp = self.client.get(reverse("paciente:agendar_cita"))
        self.assertNotIn(interno, list(resp.context["servicios"]))
        self.assertIn(self.servicio, list(resp.context["servicios"]))
        resp = self.client.get(reverse("paciente:api_slots"), {"fecha": "2030-01-07", "servicio_id": interno.id})
        self.assertEqual(resp.status_code, 404)

    def test_guia_se_descarga_en_el_idioma_activo(self):
        from django.utils import translation
        resp = self.client.get(reverse("paciente:guia"))
        self.assertTrue(resp["Location"].endswith("manual_paciente.pdf"))
        with translation.override("en"):
            url = reverse("paciente:guia")
        resp = self.client.get(url)
        self.assertTrue(resp["Location"].endswith("manual_paciente_en.pdf"))
