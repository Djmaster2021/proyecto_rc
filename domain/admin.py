from django.contrib import admin
from .models import (
    Dentista, Servicio, Paciente, Horario, Cita, Pago, 
    ComprobantePago, EncuestaSatisfaccion, Notificacion, AvisoDentista
)

admin.site.register(Dentista)
admin.site.register(Servicio)
admin.site.register(Paciente)
admin.site.register(Horario)
admin.site.register(Cita)
admin.site.register(Pago)
admin.site.register(ComprobantePago) # <--- Nueva
admin.site.register(EncuestaSatisfaccion)
admin.site.register(Notificacion)
admin.site.register(AvisoDentista)