from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from domain.models import Dentista, Paciente, Cita, Pago, Servicio


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
