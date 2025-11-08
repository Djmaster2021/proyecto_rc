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
    """Perfil extendido para pacientes."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_paciente",
        verbose_name="Usuario de Login"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    telefono = models.CharField(max_length=30, verbose_name="Teléfono")
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección")
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de Nacimiento")
    
    # Campos para futura IA
    score_riesgo = models.FloatField(default=0.0, verbose_name="Score de Riesgo (IA)", help_text="Probabilidad calculada de inasistencia")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"


class Dentista(TimeStampedModel):
    """Perfil para el dentista/administrador del consultorio."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_dentista",
        verbose_name="Usuario de Login"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    especialidad = models.CharField(max_length=120, blank=True, verbose_name="Especialidad")
    licencia = models.CharField(max_length=60, blank=True, verbose_name="Número de Licencia")

    def __str__(self):
        return f"Dr(a). {self.nombre}"

    class Meta:
        verbose_name = "Dentista"
        verbose_name_plural = "Dentistas"

# (Opcional: Si el administrador es distinto al Dentista, mantenlo. Si es el mismo, puedes borrar esto)
class Administrador(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_administrador"
    )
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.nombre

# ==============================================================================
# MODELOS DE NEGOCIO
# ==============================================================================

class Servicio(TimeStampedModel):
    """Catálogo de servicios dentales."""
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duracion_estimada = models.PositiveIntegerField(default=60, help_text="Duración en minutos", verbose_name="Duración (min)")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (${self.precio})"

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"


class Disponibilidad(models.Model):
    """Define los horarios laborales del dentista para la agenda online."""
    DIAS_SEMANA = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
        (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
    ]
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.IntegerField(choices=DIAS_SEMANA, verbose_name="Día de la semana")
    hora_inicio = models.TimeField(verbose_name="Hora inicio turno")
    hora_fin = models.TimeField(verbose_name="Hora fin turno")

    def __str__(self):
        return f"{self.get_dia_semana_display()}: {self.hora_inicio} - {self.hora_fin}"
    
    class Meta:
        verbose_name = "Horario de Disponibilidad"
        verbose_name_plural = "Horarios de Disponibilidad"


class Cita(TimeStampedModel):
    """EL NÚCLEO: Registro de citas médicas."""
    class EstadoCita(models.TextChoices):
        PENDIENTE = 'PENDIENTE', _('Pendiente de Confirmación')
        CONFIRMADA = 'CONFIRMADA', _('Confirmada')
        COMPLETADA = 'COMPLETADA', _('Completada / Asistió')
        CANCELADA_PACIENTE = 'CANCEL_PAC', _('Cancelada por Paciente')
        CANCELADA_DENTISTA = 'CANCEL_DOC', _('Cancelada por Dentista')
        NO_SHOW = 'NO_SHOW', _('No Asistió (Inasistencia)')

    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name="citas")
    dentista = models.ForeignKey(Dentista, on_delete=models.PROTECT, related_name="agenda")
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, null=True, related_name="citas")
    
    fecha_hora_inicio = models.DateTimeField(verbose_name="Inicio de Cita")
    fecha_hora_fin = models.DateTimeField(verbose_name="Fin de Cita")
    
    estado = models.CharField(
        max_length=15,
        choices=EstadoCita.choices,
        default=EstadoCita.PENDIENTE,
        verbose_name="Estado Actual"
    )
    
    notas = models.TextField(blank=True, verbose_name="Notas internas/Diagnóstico")

    def clean(self):
        if self.fecha_hora_inicio and self.fecha_hora_fin:
            if self.fecha_hora_inicio >= self.fecha_hora_fin:
                raise ValidationError("La cita no puede terminar antes de empezar.")

    def __str__(self):
        return f"Cita: {self.paciente} - {self.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['-fecha_hora_inicio']
        verbose_name = "Cita"
        verbose_name_plural = "Citas"


class Pago(TimeStampedModel):
    """Registro de pagos, preparado para integración con MercadoPago."""
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
    
    # Campos específicos para MercadoPago (referencias externas)
    mercadopago_id = models.CharField(max_length=100, blank=True, null=True, unique=True, help_text="ID de transacción de MercadoPago")

    def __str__(self):
        return f"Pago {self.id} - {self.get_estado_display()} (${self.monto})"