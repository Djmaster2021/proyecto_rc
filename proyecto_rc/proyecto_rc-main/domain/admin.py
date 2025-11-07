# domain/admin.py
from django.contrib import admin
from .models import Paciente, Dentista, Administrador, Servicio


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "email", "telefono", "direccion", "created_at")
    search_fields = ("nombre", "email", "telefono")
    list_filter = ("created_at",)
    ordering = ("nombre",)


@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "especialidad", "telefono", "email")
    search_fields = ("nombre", "especialidad", "email", "telefono")
    ordering = ("nombre",)


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "email")
    search_fields = ("nombre", "email")
    ordering = ("nombre",)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "precio", "activo", "created_at")
    search_fields = ("nombre", "descripcion")
    list_filter = ("activo",)
    ordering = ("nombre",)
