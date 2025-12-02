from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.core.signing import TimestampSigner
from domain.models import Cita
from datetime import timedelta

class Command(BaseCommand):
    help = 'Robot que envía correos de confirmación para citas de mañana.'

    def handle(self, *args, **options):
        self.stdout.write("🤖 Iniciando robot de recordatorios...")
        
        # 1. Calcular fecha de "MAÑANA"
        hoy = timezone.now().date()
        manana = hoy  # <-- Truco para probar hoy mismo
        
        # 2. Buscar citas de mañana que sigan PENDIENTES
        citas_manana = Cita.objects.filter(
            fecha_hora_inicio__date=manana,
            estado=Cita.EstadoCita.PENDIENTE
        )
        
        self.stdout.write(f"📅 Buscando citas para: {manana}")
        self.stdout.write(f"📬 Citas encontradas para recordar: {citas_manana.count()}")

        signer = TimestampSigner()
        enviados = 0

        for cita in citas_manana:
            try:
                # 3. Generar el enlace secreto único
                token = signer.sign(cita.id)
                # Construimos la URL completa (ej. http://localhost:8000/paciente/confirmar/...)
                # NOTA: En producción, cambia '127.0.0.1:8000' por tu dominio real.
                enlace_confirmar = f"http://127.0.0.1:8000{reverse('paciente:confirmar_por_email', args=[token])}"

                # 4. Redactar el correo
                asunto = '⏰ Recordatorio: Tu cita es mañana - Consultorio RC'
                mensaje = f"""
Hola {cita.paciente.nombre},

Te recordamos que tienes una cita programada para mañana.

📅 Fecha: {cita.fecha_hora_inicio.strftime('%d/%m/%Y')}
⏰ Hora: {cita.fecha_hora_inicio.strftime('%H:%M')}
🦷 Tratamiento: {cita.servicio.nombre}

IMPORTANTE: Por favor confirma tu asistencia haciendo clic en el siguiente enlace. 
Si confirmas y no asistes, se podría aplicar una penalización a tu cuenta.

👉 CLIC AQUÍ PARA CONFIRMAR ASISTENCIA:
{enlace_confirmar}

¡Nos vemos mañana!
Dr. Rodolfo Castellón
                """

                # 5. Enviar
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [cita.paciente.user.email],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Correo enviado a {cita.paciente.nombre}"))
                enviados += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error enviando a {cita.paciente.nombre}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"✨ Robot finalizado. Total enviados: {enviados}"))