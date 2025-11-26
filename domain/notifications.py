# domain/notifications.py

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

def _get_email_paciente(cita):
    """
    Devuelve el email del paciente si existe y está vinculado a un User.
    Si no hay email, regresa None y no se envía nada.
    """
    paciente = getattr(cita, "paciente", None)
    if not paciente:
        return None

    user = getattr(paciente, "user", None)
    email = getattr(user, "email", None)
    if not email:
        return None
    return email


def enviar_correo_confirmacion_cita(cita):
    """
    Se llama justo cuando se crea la cita.
    Envía un correo de confirmación con fecha, hora y servicio.
    """
    to_email = _get_email_paciente(cita)
    if not to_email:
        return  # silencioso, no hay correo del paciente

    contexto = {
        "cita": cita,
        "paciente": cita.paciente,
        "dentista": cita.dentista,
    }

    subject = "Confirmación de cita – Consultorio Dental Rodolfo Castellón"
    text_body = render_to_string("emails/cita_confirmacion.txt", contexto)
    html_body = render_to_string("emails/cita_confirmacion.html", contexto)

    send_mail(
        subject=subject,
        message=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[to_email],
        html_message=html_body,
        fail_silently=False,
    )


def enviar_correo_recordatorio_cita(cita):
    """
    Se llama ~24 horas antes de la cita.
    Envía un recordatorio sencillo.
    """
    to_email = _get_email_paciente(cita)
    if not to_email:
        return

    contexto = {
        "cita": cita,
        "paciente": cita.paciente,
        "dentista": cita.dentista,
    }

    subject = "Recordatorio de cita – Consultorio Dental Rodolfo Castellón"
    text_body = render_to_string("emails/cita_recordatorio.txt", contexto)
    html_body = render_to_string("emails/cita_recordatorio.html", contexto)

    send_mail(
        subject=subject,
        message=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[to_email],
        html_message=html_body,
        fail_silently=False,
    )

def enviar_correo_penalizacion(
    email_destino: str,
    nombre_paciente: str,
    motivo: str,
    recargo: float,
    dias_limite: int = 5,
):
    """
    Envía un correo al paciente cuando queda penalizado por inasistencias.

    Parámetros:
    - email_destino: correo del paciente.
    - nombre_paciente: nombre para personalizar el mensaje.
    - motivo: descripción de la penalización.
    - recargo: monto a pagar (ej. 300).
    - dias_limite: días para pagar antes de la baja definitiva.
    """
    subject = "Penalización por inasistencias – Consultorio Dental 'Rodolfo Castellón'"

    mensaje = (
        f"Hola {nombre_paciente},\n\n"
        f"Te informamos que se ha generado una penalización en tu cuenta por el siguiente motivo:\n"
        f"- {motivo}\n\n"
        f"Cuota a pagar: ${recargo:.2f} MXN.\n"
        f"Tienes {dias_limite} días naturales para realizar el pago. "
        "Si la cuota no se liquida dentro de ese plazo, tu cuenta será dada de baja "
        "y ya no podrás acceder al sistema. Para regularizar tu situación después "
        "de la baja, deberás ponerte en contacto directamente con el consultorio.\n\n"
        "Atentamente,\n"
        "Consultorio Dental 'Rodolfo Castellón'"
    )

    remitente = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not remitente:
        # Fallback simple por si no está configurado
        remitente = "no-reply@consultoriodental.local"

    send_mail(
        subject,
        mensaje,
        remitente,
        [email_destino],
        fail_silently=False,
    )
