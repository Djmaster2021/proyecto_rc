from django.conf import settings
from django.db import models
from django.utils import timezone


# ============================================================
# BASE ABSTRACTA: TIMESTAMP
# ============================================================

class TimeStampedModel(models.Model):
    """
    Modelo base con created_at / updated_at.
    Permitimos null para no romper tablas que ya tienen registros.
    """
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True


# ============================================================
# DENTISTA
# ============================================================

class Dentista(TimeStampedModel):
    """
    Perfil profesional del dentista.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_dentista",
    )
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=30, blank=True)
    especialidad = models.CharField(max_length=150, blank=True)
    foto_perfil = models.ImageField(
        upload_to="dentistas/fotos/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.nombre or f"Dentista #{self.pk}"


# ============================================================
# PACIENTE
# ============================================================

class Paciente(TimeStampedModel):
    """
    Perfil del paciente, ligado opcionalmente a un usuario.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="perfil_paciente",
    )
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pacientes",
    )
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    imagen = models.ImageField(upload_to="pacientes/", blank=True, null=True)

    def __str__(self):
        return self.nombre or f"Paciente #{self.pk}"


# ============================================================
# SERVICIO
# ============================================================

class Servicio(TimeStampedModel):
    """
    Tratamientos / servicios del consultorio.
    """
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="servicios",
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    # Duración “original” del modelo
    duracion_minutos = models.PositiveIntegerField(default=45)

    # Campo usado por la IA / agenda
    duracion_estimada = models.IntegerField(default=45)

    def __str__(self):
        return self.nombre


# ============================================================
# DISPONIBILIDAD (HORARIO DEL DENTISTA)
# ============================================================

class Disponibilidad(TimeStampedModel):
    """
    Bloques de horario laboral del dentista.
    Por ejemplo: Lunes 09:00–14:00.
    """

    class DiasSemana(models.IntegerChoices):
        LUNES = 0, "Lunes"
        MARTES = 1, "Martes"
        MIERCOLES = 2, "Miércoles"
        JUEVES = 3, "Jueves"
        VIERNES = 4, "Viernes"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    DIAS_SEMANA = DiasSemana.choices

    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.CASCADE,
        related_name="disponibilidades",
    )
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio}–{self.hora_fin}"


# ============================================================
# CITA
# ============================================================

class Cita(TimeStampedModel):
    """
    Cita agendada entre paciente y dentista.
    """

    class EstadoCita(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        COMPLETADA = "COMPLETADA", "Completada"
        CANCELADA = "CANCELADA", "Cancelada"
        INASISTENCIA = "INASISTENCIA", "Inasistencia"

    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.CASCADE,
        related_name="citas",
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="citas",
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="citas",
    )

    fecha_hora_inicio = models.DateTimeField()
    fecha_hora_fin = models.DateTimeField()

    estado = models.CharField(
        max_length=20,
        choices=EstadoCita.choices,
        default=EstadoCita.PENDIENTE,
    )

    # En la BD ya existían registros con NULL, así que permitimos null aquí también
    notas = models.TextField(blank=True, null=True)
    archivo_adjunto = models.FileField(
        upload_to="citas/adjuntos/",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.paciente} - {self.servicio} ({self.fecha_hora_inicio})"


# ============================================================
# PAGO
# ============================================================

class Pago(TimeStampedModel):
    """
    Registro de pago asociado a una cita.
    """

    class MetodoPago(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TARJETA = "TARJETA", "Tarjeta"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        MERCADOPAGO = "MERCADOPAGO", "MercadoPago"

    class EstadoPago(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        COMPLETADO = "COMPLETADO", "Completado"
        FALLIDO = "FALLIDO", "Fallido"

    cita = models.OneToOneField(
        Cita,
        on_delete=models.CASCADE,
        related_name="pago_relacionado",
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO,
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoPago.choices,
        default=EstadoPago.PENDIENTE,
    )

    def __str__(self):
        return f"Pago #{self.pk} - {self.monto} ({self.estado})"


# ============================================================
# NOTIFICACIONES (BARRA SUPERIOR / IN-APP)
# ============================================================

class Notificacion(TimeStampedModel):
    """
    Notificaciones internas que se muestran en el dashboard.
    """

    class Tipo(models.TextChoices):
        INFO = "info", "Información"
        WARNING = "warning", "Advertencia"
        SUCCESS = "success", "Éxito"
        ERROR = "error", "Error"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones",
    )
    # Los hacemos opcionales para no romper notificaciones antiguas
    titulo = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )
    mensaje = models.TextField(
        blank=True,
        null=True,
    )
    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
        default=Tipo.INFO,
    )
    leida = models.BooleanField(default=False)
    enviada_el = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.titulo} -> {self.usuario}"


# ============================================================
# ENCUESTA DE SATISFACCIÓN (IA + FEEDBACK)
# ============================================================

class EncuestaSatisfaccion(TimeStampedModel):
    """
    Feedback del paciente después de la cita.
    Usado por la IA para análisis de sentimiento.
    """

    class Sentimiento(models.TextChoices):
        POSITIVO = "positivo", "Positivo"
        NEUTRO = "neutro", "Neutro"
        NEGATIVO = "negativo", "Negativo"

    # Se hacen opcionales para poder migrar datos viejos
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="encuestas",
        null=True,
        blank=True,
    )
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.CASCADE,
        related_name="encuestas",
        null=True,
        blank=True,
    )
    cita = models.ForeignKey(
        Cita,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="encuesta_satisfaccion",
    )

    puntuacion = models.PositiveSmallIntegerField(
        help_text="Escala 1–5 (5 = excelente)",
        null=True,
        blank=True,
    )
    comentario = models.TextField(blank=True)
    recomendaria = models.BooleanField(
        default=True,
        help_text="Si recomendaría el consultorio.",
    )

    # Campos de IA
    sentimiento_ia = models.CharField(
        max_length=20,
        choices=Sentimiento.choices,
        blank=True,
        null=True,
        help_text="Resultado del análisis de sentimiento automático.",
    )
    metadata_ia = models.JSONField(
        blank=True,
        null=True,
        help_text="Detalles adicionales generados por la IA (scores, etiquetas, etc.)",
    )

    def __str__(self):
        return f"Encuesta {self.paciente} ({self.puntuacion}/5)"

    class Meta:
        verbose_name = "Encuesta de satisfacción"
        verbose_name_plural = "Encuestas de satisfacción"
        ordering = ["-created_at"]
