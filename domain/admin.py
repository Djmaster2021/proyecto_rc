# domain/admin.py

from django.contrib import admin
from .models import (
    Dentista,
    Paciente,
    Servicio,
    Disponibilidad,
    Cita,
    Pago,
    Notificacion,
    EncuestaSatisfaccion,
)


# ============================================================
# DENTISTA
# ============================================================

@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "telefono", "especialidad", "created_at")
    search_fields = ("nombre", "telefono", "especialidad", "user__email", "user__username")
    list_filter = ("especialidad", "created_at")
    readonly_fields = ("created_at", "updated_at")


# ============================================================
# PACIENTE
# ============================================================

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "telefono", "dentista", "fecha_nacimiento", "created_at")
    search_fields = (
        "nombre",
        "telefono",
        "direccion",
        "dentista__nombre",
        "user__email",
        "user__username",
    )
    list_filter = ("dentista", "created_at")
    readonly_fields = ("created_at", "updated_at")


# ============================================================
# SERVICIO
# ============================================================

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "dentista",
        "precio",
        "activo",
        "duracion_minutos",
        "duracion_estimada",
    )
    search_fields = ("nombre", "descripcion", "dentista__nombre")
    list_filter = ("activo", "dentista")
    readonly_fields = ("created_at", "updated_at")


# ============================================================
# DISPONIBILIDAD (HORARIO DEL DENTISTA)
# ============================================================

@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = ("id", "dentista", "dia_semana", "hora_inicio", "hora_fin")
    list_filter = ("dentista", "dia_semana")
    search_fields = ("dentista__nombre",)
    readonly_fields = ("created_at", "updated_at")


# ============================================================
# CITA
# ============================================================

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dentista",
        "paciente",
        "servicio",
        "fecha_hora_inicio",
        "fecha_hora_fin",
        "estado",
    )
    list_filter = ("estado", "dentista", "fecha_hora_inicio")
    search_fields = (
        "paciente__nombre",
        "dentista__nombre",
        "servicio__nombre",
        "notas",
    )
    readonly_fields = ("created_at", "updated_at")


# ============================================================
# PAGO
# ============================================================

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("id", "cita", "monto", "metodo", "estado", "created_at")
    list_filter = ("metodo", "estado", "created_at")
    search_fields = ("cita__paciente__nombre", "cita__dentista__nombre")
    readonly_fields = ("created_at", "updated_at")


# ============================================================
# NOTIFICACIONES
# ============================================================

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "titulo", "tipo", "leida", "enviada_el")
    list_filter = ("tipo", "leida", "enviada_el")
    search_fields = ("titulo", "mensaje", "usuario__username", "usuario__email")
    readonly_fields = ("created_at", "updated_at")


# ============================================================
# ENCUESTA DE SATISFACCIÓN
# ============================================================

@admin.register(EncuestaSatisfaccion)
class EncuestaSatisfaccionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "paciente",
        "dentista",
        "puntuacion",
        "sentimiento_ia",
        "recomendaria",
        "created_at",
    )
    list_filter = ("puntuacion", "sentimiento_ia", "recomendaria", "dentista")
    search_fields = (
        "paciente__nombre",
        "dentista__nombre",
        "comentario",
    )
    readonly_fields = ("created_at", "updated_at")
