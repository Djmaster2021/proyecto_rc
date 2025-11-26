# domain/management/commands/enviar_recordatorios_citas.py

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from domain.models import Cita
from domain.notifications import enviar_correo_recordatorio_cita


class Command(BaseCommand):
    help = "Envía recordatorios de citas aproximadamente 24 horas antes."

    def handle(self, *args, **options):
        ahora = timezone.now()
        ventana_inicio = ahora + timedelta(hours=24)
        ventana_fin = ahora + timedelta(hours=25)  # margen de 1 hora

        # Solo citas pendientes / confirmadas, sin recordatorio enviado
        qs = Cita.objects.filter(
            fecha_hora_inicio__gte=ventana_inicio,
            fecha_hora_inicio__lt=ventana_fin,
            recordatorio_24h_enviado=False,
            estado__in=[
                Cita.EstadoCita.PENDIENTE,
                Cita.EstadoCita.CONFIRMADA,
            ],
        )

        total = qs.count()
        self.stdout.write(f"Encontradas {total} citas para enviar recordatorio.")

        for cita in qs:
            try:
                enviar_correo_recordatorio_cita(cita)
                cita.recordatorio_24h_enviado = True
                cita.save(update_fields=["recordatorio_24h_enviado"])
                self.stdout.write(self.style.SUCCESS(
                    f"Recordatorio enviado a cita #{cita.id}"
                ))
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Error enviando recordatorio para cita #{cita.id}: {e}"
                    )
                )
