# ============================================================
#  MODELOS DE BASE DE DATOS (DOMAIN) — RC DENTAL PRO
# ============================================================

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone

# ============================================================
# 1. PERFIL DEL DENTISTA
# ============================================================
class Dentista(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dentista')
    nombre = models.CharField(max_length=200, help_text="Nombre completo del doctor")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    especialidad = models.CharField(max_length=100, default="Odontología General")
    licencia = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cédula Profesional")
    direccion = models.CharField(max_length=255, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    
    def __str__(self):
        return f"Dr. {self.nombre}"

# ============================================================
# 2. CATÁLOGO DE SERVICIOS
# ============================================================
class Servicio(models.Model):
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, help_text="Descripción breve del tratamiento")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_estimada = models.IntegerField(default=30, help_text="Duración en minutos")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (${self.precio})"

# ============================================================
# 3. PACIENTES
# ============================================================
class Paciente(models.Model):
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='paciente_perfil')
    nombre = models.CharField(max_length=200)
    telefono = models.CharField(max_length=10, blank=True)
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    antecedentes = models.TextField(blank=True, help_text="Alergias o enfermedades")
    
    # Campo para la foto de perfil
    imagen = models.ImageField(upload_to='pacientes/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
    
    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))

# ============================================================
# 4. HORARIOS DE TRABAJO
# ============================================================
class Horario(models.Model):
    DIAS = [
        (1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'), (4, 'Jueves'),
        (5, 'Viernes'), (6, 'Sábado'), (7, 'Domingo')
    ]
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE)
    dia_semana = models.IntegerField(choices=DIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.get_dia_semana_display()}: {self.hora_inicio} - {self.hora_fin}"

    class Meta:
        ordering = ["dentista", "dia_semana", "hora_inicio"]

# ============================================================
# 5. CITAS CLÍNICAS
# ============================================================
class Cita(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
        ('INASISTENCIA', 'No Show'),
    ]
    
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    notas = models.TextField(blank=True)
    archivo_adjunto = models.FileField(upload_to='citas_archivos/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    veces_reprogramada = models.PositiveSmallIntegerField(default=0)
    recordatorio_24h_enviado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.fecha} - {self.paciente} ({self.servicio})"

    @property
    def fecha_hora_inicio(self):
        return datetime.combine(self.fecha, self.hora_inicio)

# ============================================================
# 6. PAGOS
# ============================================================
class Pago(models.Model):
    METODOS = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
        ('MERCADOPAGO', 'MercadoPago'),
        ('MERCADOPAGO_FAKE', 'MercadoPago (fake)'),
    ]
    ESTADOS_PAGO = [
        ('PENDIENTE', 'Pendiente'),
        ('COMPLETADO', 'Completado'),
    ]
    
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name='pago_relacionado')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODOS, default='EFECTIVO')
    estado = models.CharField(max_length=20, choices=ESTADOS_PAGO, default='PENDIENTE')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago ${self.monto} - {self.cita}"

# ============================================================
# 7. COMPROBANTE DE PAGO
# ============================================================
class ComprobantePago(models.Model):
    pago = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='comprobante')
    folio = models.CharField(max_length=50, unique=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=10, default="MXN")
    datos_extra = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Comprobante {self.folio}"

class PenalizacionLog(models.Model):
    ACCIONES = [
        ("ADVERTENCIA", "Advertencia"),
        ("AUTO_PENALIZAR", "Penalización automática"),
        ("SUSPENDER", "Suspender cuenta"),
        ("REACTIVAR", "Reactivar cuenta"),
    ]
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    motivo = models.TextField(blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_accion_display()} - {self.paciente.nombre}"

# ============================================================
# 8. ENCUESTAS, NOTIFICACIONES Y AVISOS
# ============================================================

class EncuestaSatisfaccion(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE)
    cita = models.ForeignKey(Cita, on_delete=models.SET_NULL, null=True, blank=True)
    puntuacion = models.PositiveSmallIntegerField(default=5)
    comentario = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Encuesta {self.paciente} - {self.puntuacion}"

class Notificacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.titulo

class AvisoDentista(models.Model):
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE)
    mensaje = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Aviso para {self.dentista}"

# ============================================================
# 9. ODONTOGRAMA (Modelos Corregidos)
# ============================================================

# Modelo antiguo (lo mantenemos por si acaso hay datos viejos)
class OdontogramaEntrada(models.Model):
    ESTADOS = [
        ("sano", "Sano"),
        ("ortodoncia", "Ortodoncia / Bracket"),
        ("restauracion", "Restauración"),
        ("observacion", "Observación"),
    ]

    # Usamos related_name="odontograma" (El original)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="odontograma")
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE)
    numero_diente = models.CharField(max_length=4)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="sano")
    nota = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.paciente} - Diente {self.numero_diente} ({self.estado})"

# ============================================================
# 10. TICKET DE SOPORTE
# ============================================================
class TicketSoporte(models.Model):
    ESTADOS = [
        ("ABIERTO", "Abierto"),
        ("EN_PROCESO", "En proceso"),
        ("CERRADO", "Cerrado"),
    ]
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE)
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default="ABIERTO")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.id} - {self.asunto}"

    class Meta:
        ordering = ["-created_at"]

# Modelo nuevo para el Odontograma Interactivo SVG
# EN domain/models.py (Al final)

class Diente(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='dientes')
    numero = models.CharField(max_length=3)
    estado = models.CharField(max_length=20)
    
    # NUEVO CAMPO:
    nota = models.TextField(blank=True, null=True) # Aquí guardaremos el texto
    
    class Meta:
        unique_together = ('paciente', 'numero')

    def __str__(self):
        return f"{self.paciente} - Diente {self.numero}: {self.estado}"
    
    
