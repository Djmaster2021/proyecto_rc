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
            # 👇 aquí agrego "horarios"
            'keywords': ['horario', 'horarios', 'hora', 'atienden'],
            'respuesta': 'Nuestro horario de atención es de **Lunes a Sábado de 9:00 AM a 7:00 PM**.'
        },
        {
            # tus botones mandan "ubicacion"
            'keywords': ['ubicacion', 'ubicación', 'direccion', 'dirección', 'llegar'],
            'respuesta': 'Estamos ubicados en **Calle Guatemala #125, El Pitillal, Puerto Vallarta**. ¡Puedes encontrarnos en el mapa de esta página!'
        },
        {
            # 👇 agrego "precios" y "costos"
            'keywords': ['precio', 'precios', 'costo', 'costos', 'valor', 'cuanto', 'cuánto'],
            'respuesta': 'Los precios varían según el tratamiento. Una limpieza básica comienza en $800. ¡Agenda una cita para una valoración gratuita!'
        },
        {
            'keywords': ['cita', 'citas', 'agendar', 'agendo', 'turno'],
            'respuesta': 'Puedes agendar tu cita directamente en la sección "Agendar tu cita" de esta web. Solo necesitas registrarte. ¡Es muy fácil!'
        },
        {
            'keywords': ['servicio', 'servicios', 'tratamiento', 'tratamientos'],
            'respuesta': 'Ofrecemos Odontología General, Estética Dental, Limpiezas, Endodoncia, y Ortodoncia. ¿Qué necesitas revisar?'
        },
        {
            'keywords': ['telefono', 'teléfono', 'whatsapp', 'llamar', 'numero'],
            'respuesta': 'Nuestro WhatsApp es: 322 889 2558.'
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
