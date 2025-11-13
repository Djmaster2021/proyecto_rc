# domain/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

User = get_user_model()

class TimeStampedModel(models.Model):
    """Modelo abstracto que añade campos de auditoría temporal."""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")

    class Meta:
        abstract = True

# ==============================================================================
# PERFILES DE USUARIO
# ==============================================================================

class Paciente(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_paciente",
        verbose_name="Usuario de Login"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    telefono = models.CharField(max_length=30, verbose_name="Teléfono")
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección")
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de Nacimiento")
    score_riesgo = models.FloatField(default=0.0, verbose_name="Score de Riesgo (IA)", help_text="Probabilidad calculada de inasistencia")

    def __str__(self): return self.nombre

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"


class Dentista(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_dentista",
        verbose_name="Usuario de Login"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    especialidad = models.CharField(max_length=120, blank=True, verbose_name="Especialidad")
    licencia = models.CharField(max_length=60, blank=True, verbose_name="Número de Licencia")

    def __str__(self): return f"Dr(a). {self.nombre}"

    class Meta:
        verbose_name = "Dentista"
        verbose_name_plural = "Dentistas"

class Administrador(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_administrador")
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=30, blank=True)
    def __str__(self): return self.nombre

# ==============================================================================
# MODELOS DE NEGOCIO
# ==============================================================================

class Servicio(TimeStampedModel):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duracion_estimada = models.PositiveIntegerField(default=60, help_text="Duración en minutos", verbose_name="Duración (min)")
    activo = models.BooleanField(default=True)

    def __str__(self): return f"{self.nombre} (${self.precio})"

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"


class Disponibilidad(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
        (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
    ]
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.IntegerField(choices=DIAS_SEMANA, verbose_name="Día de la semana")
    hora_inicio = models.TimeField(verbose_name="Hora inicio turno")
    hora_fin = models.TimeField(verbose_name="Hora fin turno")

    def __str__(self): return f"{self.get_dia_semana_display()}: {self.hora_inicio} - {self.hora_fin}"
    
    class Meta:
        verbose_name = "Horario de Disponibilidad"
        verbose_name_plural = "Horarios de Disponibilidad"


class Cita(TimeStampedModel):
    class EstadoCita(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de Confirmación'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada (General)' 
        CONFIRMADA_PACIENTE = 'CONF_PACIENTE', 'Confirmada por Paciente (Email)'
        CONFIRMADA_DENTISTA = 'CONF_DENTISTA', 'Confirmada por Dentista'
        COMPLETADA = 'COMPLETADA', 'Completada / Asistió'
        CANCELADA = 'CANCELADA', 'Cancelada General'
        CANCELADA_PACIENTE = 'CANCEL_PAC', 'Cancelada por Paciente'
        CANCELADA_DENTISTA = 'CANCEL_DOC', 'Cancelada por Dentista'
        NO_SHOW = 'NO_SHOW', 'No Asistió (Falta)'

    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name="citas")
    dentista = models.ForeignKey(Dentista, on_delete=models.PROTECT, related_name="agenda")
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, null=True, related_name="citas")
    
    fecha_hora_inicio = models.DateTimeField(verbose_name="Inicio de Cita")
    fecha_hora_fin = models.DateTimeField(verbose_name="Fin de Cita")
    
    estado = models.CharField(
        max_length=15, choices=EstadoCita.choices, default=EstadoCita.PENDIENTE, verbose_name="Estado Actual"
    )
    notas = models.TextField(blank=True, verbose_name="Notas internas/Diagnóstico")

    # --- NUEVO CAMPO PARA TU REGLA DE NEGOCIO ---
    veces_reprogramada = models.PositiveIntegerField(default=0, verbose_name="Veces modificada")

    def clean(self):
        if self.fecha_hora_inicio and self.fecha_hora_fin:
            if self.fecha_hora_inicio >= self.fecha_hora_fin:
                raise ValidationError("La cita no puede terminar antes de empezar.")

    def __str__(self): return f"Cita: {self.paciente} - {self.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['-fecha_hora_inicio']
        verbose_name = "Cita"
        verbose_name_plural = "Citas"


class Pago(TimeStampedModel):
    class MetodoPago(models.TextChoices):
        EFECTIVO = 'EFECTIVO', _('Efectivo en Consultorio')
        MERCADOPAGO = 'MERCADOPAGO', _('MercadoPago Online')
        TRANSFERENCIA = 'TRANSFERENCIA', _('Transferencia Bancaria')

    class EstadoPago(models.TextChoices):
        PENDIENTE = 'PENDIENTE', _('Pendiente')
        COMPLETADO = 'COMPLETADO', _('Pagado')
        FALLIDO = 'FALLIDO', _('Fallido/Rechazado')
        REEMBOLSADO = 'REEMBOLSADO', _('Reembolsado')

    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name="pago_relacionado")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Total")
    metodo = models.CharField(max_length=20, choices=MetodoPago.choices, default=MetodoPago.EFECTIVO)
    estado = models.CharField(max_length=20, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE)
    mercadopago_id = models.CharField(max_length=100, blank=True, null=True, unique=True, help_text="ID de transacción de MercadoPago")

    def __str__(self): return f"Pago {self.id} - {self.get_estado_display()} (${self.monto})"
    

class EncuestaSatisfaccion(TimeStampedModel):
    class Sentimiento(models.TextChoices):
        POSITIVO = 'POS', 'Positivo 😊'
        NEUTRAL = 'NEU', 'Neutral 😐'
        NEGATIVO = 'NEG', 'Negativo 😡'

    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name="encuesta")
    calificacion = models.PositiveIntegerField(verbose_name="Estrellas (1-5)", choices=[(i, str(i)) for i in range(1, 6)])
    comentario = models.TextField(blank=True, verbose_name="Opinión del Paciente")
    sentimiento_ia = models.CharField(max_length=3, choices=Sentimiento.choices, default=Sentimiento.NEUTRAL, verbose_name="Análisis IA")
    es_publico = models.BooleanField(default=False, verbose_name="Visible en Landing Page")

    def __str__(self): return f"Reseña de {self.cita.paciente} - {self.calificacion}⭐"

    class Meta:
        verbose_name = "Encuesta de Satisfacción"
        verbose_name_plural = "Encuestas de Satisfacción"


class Penalizacion(TimeStampedModel):
    class TipoPenalizacion(models.TextChoices):
        NO_SHOW = 'NO_SHOW', _('Inasistencia (No-Show)')
        CANCELACION_TARDIA = 'CANCEL_TARDIA', _('Cancelación Tardia (<24h)')

    class EstadoPenalizacion(models.TextChoices):
        PENDIENTE = 'PENDIENTE', _('Pendiente de Pago')
        LIQUIDADA = 'LIQUIDADA', _('Liquidada')
        PERDONADA = 'PERDONADA', _('Perdonada (Admin)')

    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name="penalizaciones", verbose_name="Paciente")
    cita = models.ForeignKey(Cita, on_delete=models.SET_NULL, related_name="penalizaciones", null=True, blank=True, verbose_name="Cita Incumplida")
    tipo = models.CharField(max_length=20, choices=TipoPenalizacion.choices, verbose_name="Motivo")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto del Recargo")
    estado = models.CharField(max_length=20, choices=EstadoPenalizacion.choices, default=EstadoPenalizacion.PENDIENTE, verbose_name="Estado de Pago")
    
    def __str__(self): return f"Penalización a {self.paciente.nombre} por {self.get_tipo_display()} (${self.monto})"

    class Meta:
        verbose_name = "Penalización"
        verbose_name_plural = "Penalizaciones"


class Notificacion(TimeStampedModel):
    class Canal(models.TextChoices):
        EMAIL = 'EMAIL', _('Correo Electrónico')
        PUSH = 'PUSH', _('Notificación Push')
        SMS = 'SMS', _('Mensaje SMS')

    class Tipo(models.TextChoices):
        RECORDATORIO = 'RECORDATORIO', _('Recordatorio de Cita')
        CONFIRMACION = 'CONFIRMACION', _('Confirmación de Cita')
        CANCELACION = 'CANCELACION', _('Cancelación de Cita')
        PAGO = 'PAGO', _('Confirmación de Pago')
        PENALIZACION = 'PENALIZACION', _('Aviso de Penalización')
        MARKETING = 'MARKETING', _('Promoción')

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notificaciones", verbose_name="Usuario")
    cita = models.ForeignKey(Cita, on_delete=models.SET_NULL, null=True, blank=True, related_name="notificaciones", verbose_name="Cita Relacionada")
    canal = models.CharField(max_length=10, choices=Canal.choices, verbose_name="Canal de Envío")
    tipo = models.CharField(max_length=20, choices=Tipo.choices, verbose_name="Tipo de Notificación")
    enviada_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Envío")
    contenido = models.TextField(blank=True, verbose_name="Contenido (o payload)")
    leida = models.BooleanField(default=False, verbose_name="Leída por el usuario")

    def __str__(self): return f"Notificación ({self.get_canal_display()}) para {self.usuario.username} sobre {self.get_tipo_display()}"

    class Meta:
        ordering = ['-enviada_el']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"