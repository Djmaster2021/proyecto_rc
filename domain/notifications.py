# domain/notifications.py

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.signing import TimestampSigner
from django.urls import reverse

from .models import AvisoDentista

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


def _enviar_email(subject, text_body, html_body, destinatarios):
    """
    Envoltura centralizada que respeta SEND_EMAILS para evitar envíos accidentales.
    """
    if not getattr(settings, "SEND_EMAILS", True):
        print("[EMAIL] SEND_EMAILS=False; correo omitido.")
        return

    remitente = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    if not remitente:
        print("[EMAIL] Sin remitente configurado; correo omitido.")
        return

    send_mail(
        subject=subject,
        message=text_body,
        from_email=remitente,
        recipient_list=destinatarios,
        html_message=html_body,
        fail_silently=False,
    )


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

    try:
        signer = TimestampSigner()
        token = signer.sign(cita.id)
        base = getattr(settings, "SITE_BASE_URL", "http://127.0.0.1:8000")
        contexto["confirm_url"] = f"{base}{reverse('paciente:confirmar_por_email', args=[token])}"
    except Exception:
        contexto["confirm_url"] = None

    subject = "Confirmación de cita – Consultorio Dental Rodolfo Castellón"
    text_body = render_to_string("emails/cita_confirmacion.txt", contexto)
    html_body = render_to_string("emails/cita_confirmacion.html", contexto)

    _enviar_email(subject, text_body, html_body, [to_email])


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

    try:
        signer = TimestampSigner()
        token = signer.sign(cita.id)
        base = getattr(settings, "SITE_BASE_URL", "http://127.0.0.1:8000")
        contexto["confirm_url"] = f"{base}{reverse('paciente:confirmar_por_email', args=[token])}"
    except Exception:
        contexto["confirm_url"] = None

    subject = "Recordatorio de cita – Consultorio Dental Rodolfo Castellón"
    text_body = render_to_string("emails/cita_recordatorio.txt", contexto)
    html_body = render_to_string("emails/cita_recordatorio.html", contexto)

    _enviar_email(subject, text_body, html_body, [to_email])

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

    _enviar_email(subject, mensaje, None, [email_destino])


def enviar_correo_ticket_soporte(dentista, asunto: str, mensaje: str):
    """
    Envía un correo al buzón de soporte interno cuando se crea un ticket.
    """
    destino = "diegomag2996@gmail.com"
    subject = f"[Soporte] {asunto} – {getattr(dentista, 'nombre', 'Dentista')}"
    contexto = {
        "dentista": dentista,
        "asunto": asunto,
        "mensaje": mensaje,
        "email_dentista": getattr(getattr(dentista, "user", None), "email", ""),
        "telefono": getattr(dentista, "telefono", ""),
    }
    html_body = render_to_string("emails/ticket_soporte.html", contexto)
    text_body = strip_tags(html_body)
    _enviar_email(subject, text_body, html_body, [destino])


def registrar_aviso_dentista(dentista, mensaje: str):
    """
    Guarda un aviso para el panel del dentista. Se mantiene simple para evitar
    dependencias con el resto del flujo.
    """
    if not dentista or not mensaje:
        return None

    texto = mensaje.strip()
    if not texto:
        return None

    try:
        return AvisoDentista.objects.create(
            dentista=dentista,
            mensaje=texto[:500],  # evitamos avisos excesivamente largos
        )
    except Exception as exc:
        print(f"[WARN] No se pudo registrar aviso: {exc}")
        return None
