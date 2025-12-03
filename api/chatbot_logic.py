# api/chatbot_logic.py
from django.utils.html import strip_tags
import re

def obtener_respuesta_bot(mensaje_usuario):
    mensaje = mensaje_usuario.lower().strip()

    reglas = [
        {
            'keywords': ['hola', 'saludo', 'buenas'],
            'respuesta': '¡Hola! Soy Asistente RC, tu asistente virtual. ¿En qué puedo ayudarte hoy? 😊'
        },
        {
            'keywords': ['pagar', 'pago', 'pagos', 'tarjeta', 'efectivo', 'transferencia', 'deposito', 'depósito', 'spei'],
            'respuesta': 'Puedes pagar en la clínica con tarjeta o efectivo. Si prefieres anticipar tu pago, escríbenos y te compartimos la cuenta para transferencia/SPEI. Recuerda poner tu nombre completo en la referencia.'
        },
        {
            'keywords': ['horario', 'horarios', 'hora', 'atienden'],
            'respuesta': 'Nuestro horario de atención es de **Lunes a Sábado de 9:00 AM a 7:00 PM**.'
        },
        {
            'keywords': ['ubicacion', 'ubicación', 'direccion', 'dirección', 'llegar'],
            'respuesta': 'Estamos ubicados en **Calle Guatemala #125, El Pitillal, Puerto Vallarta**. ¡Puedes encontrarnos en el mapa de esta página!'
        },
        {
            'keywords': ['precio', 'precios', 'costo', 'costos', 'valor', 'cuanto', 'cuánto'],
            'respuesta': 'Ejemplos de precios: Limpieza completa $800, Resina por caries desde $1,200, Blanqueamiento en clínica $3,200, Endodoncia desde $3,500 por pieza. Para presupuesto exacto agenda valoración.'
        },
        {
            'keywords': ['servicio', 'servicios', 'tratamiento', 'tratamientos'],
            'respuesta': 'Atendemos: Limpieza dental, Resinas/curaciones, Blanqueamiento, Extracciones simples, Endodoncia, Coronas, Ortodoncia (brackets y alineadores). ¿Qué te interesa revisar?'
        },
        {
            'keywords': ['limpieza', 'profilaxis'],
            'respuesta': 'La limpieza profesional incluye ultrasonido y pulido. Precio: $800. Recomendamos hacerla cada 6 meses.'
        },
        {
            'keywords': ['caries', 'resina', 'relleno', 'empaste'],
            'respuesta': 'Tratamos caries con resina fotocurable. Precio habitual: desde $1,200 por pieza, según tamaño y profundidad.'
        },
        {
            'keywords': ['blanqueamiento', 'blanqueo'],
            'respuesta': 'Blanqueamiento en clínica con lámpara fría: $3,200. Incluye valoración previa y protección de encías.'
        },
        {
            'keywords': ['extraccion', 'extracción', 'sacar muela', 'quitar muela'],
            'respuesta': 'Extracción simple desde $1,000. Si es cirugía (muela del juicio, retenida) se valora en consulta para cotizar con precisión.'
        },
        {
            'keywords': ['endodoncia', 'conducto'],
            'respuesta': 'Endodoncia (tratamiento de conductos) desde $3,500 por pieza, incluye medicación y obturación. Se cotiza mejor en valoración.'
        },
        {
            'keywords': ['corona', 'coronas', 'funda', 'fundas'],
            'respuesta': 'Corona de porcelana/zirconia desde $4,500. Incluye preparación, pruebas y colocación final.'
        },
        {
            'keywords': ['ortodoncia', 'brackets', 'alineador', 'alineadores'],
            'respuesta': 'Ortodoncia con brackets metálicos desde $800 al mes después de colocación inicial. También trabajamos alineadores: cotizamos en valoración.'
        },
        {
            'keywords': ['telefono', 'teléfono', 'whatsapp', 'llamar', 'numero'],
            'respuesta': 'Nuestro WhatsApp es: 322 889 2558.'
        },
        {
            'keywords': ['cita', 'citas', 'agendar', 'agendo', 'turno'],
            'respuesta': 'Puedes agendar tu cita directamente en la sección "Agendar tu cita" de esta web. Solo necesitas registrarte. ¡Es muy fácil!'
        },
        {
            'keywords': ['gracias', 'agradecido', 'agradecida', 'gracias!'],
            'respuesta': '¡Un placer ayudarte! ¡Estamos para servirte! 🦷💙'
        },
    ]

    for regla in reglas:
        for keyword in regla['keywords']:
            if re.search(r'\b' + re.escape(keyword) + r'\b', mensaje):
                return regla['respuesta']

    return 'Aún estoy aprendiendo y no entendí tu pregunta. 😅 Puedes intentar con palabras más sencillas como "horario", "dirección" o "precios".'
