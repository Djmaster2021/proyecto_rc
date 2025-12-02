from datetime import date, time

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from domain.models import Cita, Dentista, Horario, Paciente, Servicio


class AgendaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="doc", password="pass123")
        self.dentista = Dentista.objects.create(user=self.user, nombre="Dr. Test")
        self.client = Client()
        self.client.login(username="doc", password="pass123")

        self.paciente = Paciente.objects.create(dentista=self.dentista, nombre="Rodolfo Castellon")
        self.servicio = Servicio.objects.create(dentista=self.dentista, nombre="Limpieza", precio=100, duracion_estimada=30)

        today = date.today()
        Horario.objects.create(dentista=self.dentista, dia_semana=today.isoweekday(), hora_inicio=time(9, 0), hora_fin=time(17, 0))

    def test_agenda_filtra_por_dentista(self):
        other_user = User.objects.create_user(username="otro", password="pass123")
        other_dent = Dentista.objects.create(user=other_user, nombre="Otro")
        Paciente.objects.create(dentista=other_dent, nombre="Ajeno")
        Cita.objects.create(dentista=other_dent, paciente=self.paciente, servicio=self.servicio,
                            fecha=date.today(), hora_inicio=time(10, 0), hora_fin=time(10, 30))

        resp = self.client.get(reverse("dentista:agenda"))
        self.assertEqual(resp.status_code, 200)
        semanas = resp.context["semanas"]
        self.assertTrue(all(all(c["obj"].dentista == self.dentista for c in dia["citas"]) for semana in semanas for dia in semana))

    def test_crear_cita_rechaza_pasado(self):
        past = date.today() - timezone.timedelta(days=1)
        payload = {
            "paciente": self.paciente.id,
            "servicio": self.servicio.id,
            "fecha": past.strftime("%Y-%m-%d"),
            "hora": "10:00",
        }
        resp = self.client.post(reverse("dentista:crear_cita_manual"), data=payload, follow=True)
        self.assertEqual(Cita.objects.count(), 0)
        self.assertContains(resp, "fecha pasada", status_code=200)

    def test_slots_requieren_servicio_del_dentista(self):
        other_user = User.objects.create_user(username="otro2", password="pass123")
        other_dent = Dentista.objects.create(user=other_user, nombre="Otro2")
        other_service = Servicio.objects.create(dentista=other_dent, nombre="Otro", precio=50, duracion_estimada=30)

        today = date.today().strftime("%Y-%m-%d")
        resp = self.client.get(reverse("dentista:get_slots"), {"fecha": today, "servicio_id": other_service.id})
        self.assertJSONEqual(resp.content.decode(), {"slots": []})
