from django.utils.html import strip_tags
import re

def obtener_respuesta_bot(mensaje_usuario):
    """
    Analiza el mensaje del usuario y devuelve la mejor respuesta predefinida.
    Usa coincidencia de palabras clave inteligente.
    """
    mensaje = mensaje_usuario.lower().strip()

    # BASE DE CONOCIMIENTO (Reglas)
    # Formato: { 'palabras_clave': ['keyword1', 'keyword2'], 'respuesta': '...' }
    reglas = [
        {
            'keywords': ['hola', 'buenos dias', 'buenas tardes', 'hey'],
            'respuesta': '¡Hola! Soy el asistente virtual de Dental RC. ¿En qué puedo ayudarte hoy? 😊'
        },
        {
            'keywords': ['horario', 'hora', 'abierto', 'cierran'],
            'respuesta': 'Nuestro horario de atención es de Lunes a Sábado, de 2:00 PM a 8:00 PM.'
        },
        {
            'keywords': ['ubicacion', 'donde', 'direccion', 'llegar', 'calle'],
            'respuesta': 'Estamos en Calle Guatemala #125, Col. El Toro, Puerto Vallarta. ¡Te esperamos!'
        },
        {
            'keywords': ['precio', 'costo', 'cuanto cuesta', 'valor'],
            'respuesta': 'Los precios varían según el tratamiento. Una limpieza básica comienza en $800. Puedes ver todos los precios registrándote en nuestro portal.'
        },
        {
            'keywords': ['cita', 'agendar', 'turno'],
            'respuesta': 'Puedes agendar tu cita directamente aquí en nuestra web. Solo necesitas registrarte e iniciar sesión. ¡Es rápido y fácil!'
        },
        {
            'keywords': ['telefono', 'celular', 'whatsapp', 'llamar'],
            'respuesta': 'Nuestro WhatsApp y teléfono es: 322 889 2558.'
        },
        {
            'keywords': ['gracias', 'agradecido'],
            'respuesta': '¡Es un placer ayudarte! Estamos para servirte. 🦷💙'
        }
    ]

    # BUSCAR COINCIDENCIA
    for regla in reglas:
        for keyword in regla['keywords']:
            # Buscamos la palabra clave como palabra completa para evitar falsos positivos
            if re.search(r'\b' + re.escape(keyword) + r'\b', mensaje):
                return regla['respuesta']

    # RESPUESTA POR DEFECTO (Si no entendió)
    return 'Aún estoy aprendiendo y no entendí tu pregunta. 😅 Puedes intentar con palabras más sencillas como "horario", "dirección" o "precios".'