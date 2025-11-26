from django.contrib import admin
from .models import Paciente, Dentista, Servicio, Cita, Pago, Disponibilidad

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'get_email', 'telefono', 'score_riesgo', 'created_at')
    search_fields = ('nombre', 'user__email', 'telefono')
    list_filter = ('score_riesgo',)

    # Función auxiliar para mostrar el email desde el modelo User relacionado
    @admin.display(description='Email (Usuario)')
    def get_email(self, obj):
        return obj.user.email if obj.user else '---'

@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especialidad', 'licencia', 'get_email')
    search_fields = ('nombre', 'especialidad')

    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.user.email if obj.user else '---'

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'duracion_estimada', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha_hora_inicio', 'estado', 'dentista', 'servicio')
    list_filter = ('estado', 'fecha_hora_inicio', 'dentista')
    search_fields = ('paciente__nombre', 'paciente__user__email', 'notas')
    date_hierarchy = 'fecha_hora_inicio'

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cita', 'monto', 'metodo', 'estado', 'updated_at')
    list_filter = ('estado', 'metodo', 'created_at')
    search_fields = ('cita__paciente__nombre', 'mercadopago_id')

@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = ('dentista', 'get_dia_semana_display', 'hora_inicio', 'hora_fin')
    list_filter = ('dentista', 'dia_semana')