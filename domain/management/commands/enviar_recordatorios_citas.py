from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from domain.models import Cita
from domain.notifications import enviar_correo_recordatorio_cita


class Command(BaseCommand):
    help = "Envía recordatorios de citas aproximadamente 24 horas antes."

    def handle(self, *args, **options):
        ahora = timezone.now()
        tz = timezone.get_current_timezone()
        ventana_inicio = ahora + timedelta(hours=23)
        ventana_fin = ahora + timedelta(hours=25)

        qs = Cita.objects.filter(
            fecha__gte=ahora.date(),
            fecha__lte=ventana_fin.date(),
            estado__in=["PENDIENTE", "CONFIRMADA"],
            recordatorio_24h_enviado=False,
        )

        total = qs.count()
        enviados = 0
        self.stdout.write(f"Encontradas {total} citas candidatas para recordatorio.")

        for cita in qs:
            dt_naive = datetime.combine(cita.fecha, cita.hora_inicio)
            dt_inicio = (
                timezone.make_aware(dt_naive, tz) if timezone.is_naive(dt_naive) else dt_naive
            )

            if not (ventana_inicio <= dt_inicio <= ventana_fin):
                continue

            try:
                enviar_correo_recordatorio_cita(cita)
                cita.recordatorio_24h_enviado = True
                cita.save(update_fields=["recordatorio_24h_enviado"])
                enviados += 1
                self.stdout.write(self.style.SUCCESS(f"Recordatorio enviado a cita #{cita.id}"))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(
                    f"Error enviando recordatorio para cita #{cita.id}: {exc}"
                ))

        self.stdout.write(self.style.SUCCESS(f"Proceso finalizado. Total enviados: {enviados}"))
