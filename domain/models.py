# domain/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")

    class Meta:
        abstract = True


class Paciente(TimeStampedModel):
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre", "id"]
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"


class Dentista(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="dentista_domain"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True)
    especialidad = models.CharField(max_length=120, blank=True)
    licencia = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre", "id"]
        verbose_name = "Dentista"
        verbose_name_plural = "Dentistas"


class Administrador(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="administrador_domain"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre", "id"]
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"


class Servicio(TimeStampedModel):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["nombre", "id"]
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"