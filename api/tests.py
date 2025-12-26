from datetime import datetime, timedelta, time
import os
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from domain.models import Dentista, Paciente, Servicio, Horario, Cita, Pago


class HealthCheckTests(TestCase):
    def test_health_endpoint_ok(self):
        client = APIClient()
        resp = client.get(reverse("api_health"))
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body.get("status"), "ok")

    def test_health_endpoint_extended_with_token(self):
        client = APIClient()
        with mock.patch.dict(os.environ, {"HEALTH_TOKEN": "secret"}):
            resp = client.get(reverse("api_health"), HTTP_X_HEALTH_TOKEN="secret")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("allowed_hosts", body)


class CitasAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="apiuser", password="pass123")
        self.doc_user = User.objects.create_user(username="doctor", password="pass123")
        self.dentista = Dentista.objects.create(user=self.doc_user, nombre="Dr API")
        self.paciente = Paciente.objects.create(user=self.user, dentista=self.dentista, nombre="Paciente API")
        self.servicio = Servicio.objects.create(
            dentista=self.dentista,
            nombre="Limpieza",
            precio=500,
            duracion_estimada=30,
            activo=True,
        )
        self.fecha = self._proxima_fecha_habil()
        Horario.objects.create(
            dentista=self.dentista,
            dia_semana=self.fecha.isoweekday(),
            hora_inicio=time(9, 0),
            hora_fin=time(17, 0),
        )
        self.client.force_authenticate(user=self.user)

    def _proxima_fecha_habil(self):
        base = timezone.localdate() + timedelta(days=1)
        while base.weekday() == 6:  # domingo
            base += timedelta(days=1)
        return base

    def test_crear_cita_api_ok(self):
        url = reverse("api_crear_cita")
        resp = self.client.post(
            url,
            {
                "servicio_id": self.servicio.id,
                "fecha": self.fecha.isoformat(),
                "hora": "10:00",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)

        cita = Cita.objects.get()
        self.assertEqual(cita.dentista, self.dentista)
        self.assertEqual(cita.servicio, self.servicio)
        self.assertEqual(cita.estado, "PENDIENTE")
        self.assertTrue(Pago.objects.filter(cita=cita, estado="PENDIENTE").exists())

    def test_crear_cita_bloqueado_por_penalizacion(self):
        cita_prev = Cita.objects.create(
            dentista=self.dentista,
            paciente=self.paciente,
            servicio=self.servicio,
            fecha=self.fecha - timedelta(days=1),
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
            estado="INASISTENCIA",
        )
        Pago.objects.create(
            cita=cita_prev,
            monto=300,
            metodo="EFECTIVO",
            estado="PENDIENTE",
        )

        url = reverse("api_crear_cita")
        resp = self.client.post(
            url,
            {
                "servicio_id": self.servicio.id,
                "fecha": self.fecha.isoformat(),
                "hora": "11:00",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(Cita.objects.filter(estado="PENDIENTE").count(), 0)

    def test_slots_disponibles_requiere_auth(self):
        anon = APIClient()
        url = reverse("api_slots")
        resp = anon.get(url)
        self.assertEqual(resp.status_code, 401)

    def test_slots_disponibles_ok(self):
        url = reverse("api_slots")
        resp = self.client.get(
            url,
            {
                "fecha": self.fecha.isoformat(),
                "servicio_id": self.servicio.id,
                "dentista_id": self.dentista.id,
            },
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertIn("slots", body)

    def test_slots_rechaza_fecha_pasada(self):
        url = reverse("api_slots")
        resp = self.client.get(
            url,
            {
                "fecha": (self.fecha - timedelta(days=2)).isoformat(),
                "servicio_id": self.servicio.id,
                "dentista_id": self.dentista.id,
            },
        )
        self.assertEqual(resp.status_code, 400)

    def test_cancelar_cita_permiso(self):
        cita = Cita.objects.create(
            dentista=self.dentista,
            paciente=self.paciente,
            servicio=self.servicio,
            fecha=self.fecha,
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            estado="PENDIENTE",
        )
        url = reverse("api_cancelar_cita", args=[cita.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, "CANCELADA")

    def test_cancelar_cita_sin_auth(self):
        cita = Cita.objects.create(
            dentista=self.dentista,
            paciente=self.paciente,
            servicio=self.servicio,
            fecha=self.fecha,
            hora_inicio=time(11, 0),
            hora_fin=time(11, 30),
            estado="PENDIENTE",
        )
        anon = APIClient()
        url = reverse("api_cancelar_cita", args=[cita.id])
        resp = anon.post(url)
        self.assertEqual(resp.status_code, 401)
