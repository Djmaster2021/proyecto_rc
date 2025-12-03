from datetime import datetime, timedelta, time, date
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.management import call_command

from domain.ai_services import calcular_score_riesgo, calcular_penalizacion_paciente
from domain.models import Dentista, Paciente, Cita, Pago, Servicio


class RiesgoYPenalizacionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pac1", password="test")
        self.dentista = Dentista.objects.create(user=User.objects.create_user(username="doc", password="pwd"), nombre="Dr Test")
        self.paciente = Paciente.objects.create(user=self.user, dentista=self.dentista, nombre="Pac Uno")
        self.servicio = Servicio.objects.create(dentista=self.dentista, nombre="Consulta", precio=100, duracion_estimada=30)

    def test_score_riesgo_combina_inasistencias_cancelaciones_reprogramaciones_y_pagos(self):
        # 1 inasistencia, 1 cancelada, 1 reprogramada, 1 pago pendiente
        Cita.objects.create(
            dentista=self.dentista,
            paciente=self.paciente,
            servicio=self.servicio,
            fecha=date.today(),
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
            estado="INASISTENCIA",
            veces_reprogramada=1,
        )
        Cita.objects.create(
            dentista=self.dentista,
            paciente=self.paciente,
            servicio=self.servicio,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            estado="CANCELADA",
        )
        Pago.objects.create(
            cita=Cita.objects.create(
                dentista=self.dentista,
                paciente=self.paciente,
                servicio=self.servicio,
                fecha=date.today(),
                hora_inicio=time(11, 0),
                hora_fin=time(11, 30),
                estado="PENDIENTE",
            ),
            monto=300,
            estado="PENDIENTE",
        )

        score = calcular_score_riesgo(self.paciente)
        # Pesos: inasistencia 5, cancelada 2, reprogramada 1, pago pendiente 3 => 11 * 8 = 88
        self.assertEqual(score, 88)

    def test_penalizacion_detecta_pago_pendiente_por_inasistencias(self):
        cita = Cita.objects.create(
            dentista=self.dentista,
            paciente=self.paciente,
            servicio=self.servicio,
            fecha=date.today(),
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
            estado="INASISTENCIA",
        )
        Pago.objects.create(cita=cita, monto=300, estado="PENDIENTE")

        info = calcular_penalizacion_paciente(self.paciente)
        self.assertEqual(info["estado"], "pending")
        self.assertEqual(info["recargo"], 300)
        self.assertGreaterEqual(info["dias_restantes"], 0)


class RecordatoriosCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pac2", password="test")
        self.dentista = Dentista.objects.create(user=User.objects.create_user(username="doc2", password="pwd2"), nombre="Dr Notifier")
        self.paciente = Paciente.objects.create(user=self.user, dentista=self.dentista, nombre="Pac Dos")
        self.servicio = Servicio.objects.create(dentista=self.dentista, nombre="Control", precio=200, duracion_estimada=30)

    @patch("domain.management.commands.enviar_recordatorios_citas.enviar_correo_recordatorio_cita")
    @patch("domain.management.commands.enviar_recordatorios_citas.timezone.now")
    def test_comando_envia_recordatorio_y_marca_flag(self, mock_now, mock_email):
        base = timezone.make_aware(datetime(2025, 1, 1, 10, 0, 0))
        mock_now.return_value = base

        fecha_cita = (base + timedelta(days=1)).date()  # 23-25h ventana
        Cita.objects.create(
            dentista=self.dentista,
            paciente=self.paciente,
            servicio=self.servicio,
            fecha=fecha_cita,
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            estado="CONFIRMADA",
            recordatorio_24h_enviado=False,
        )

        call_command("enviar_recordatorios_citas")

        self.assertTrue(mock_email.called)
        cita = Cita.objects.first()
        cita.refresh_from_db()
        self.assertTrue(cita.recordatorio_24h_enviado)
