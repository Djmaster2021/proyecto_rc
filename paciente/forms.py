from django import forms
from domain.models import Paciente

class PacientePerfilForm(forms.ModelForm):
    # Campos de solo lectura (para mostrar pero no editar)
    email = forms.CharField(disabled=True, required=False, label="Correo Electrónico")
    telefono = forms.CharField(disabled=True, required=False, label="Teléfono (Contactar a soporte para cambiar)")

    class Meta:
        model = Paciente
        fields = ['imagen', 'fecha_nacimiento', 'direccion']
        labels = {
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'direccion': 'Dirección de Domicilio',
            'imagen': 'Foto de Perfil'
        }
        widgets = {
            'direccion': forms.TextInput(attrs={'class': 'cyber-input', 'placeholder': 'Calle, Número, Colonia'}),
            # Usaremos Flatpickr para la fecha
            'fecha_nacimiento': forms.TextInput(attrs={'class': 'cyber-input', 'id': 'fecha_nacimiento'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Recibimos el usuario para llenar el email
        super().__init__(*args, **kwargs)
        
        # Estilos CSS para el campo de imagen
        self.fields['imagen'].widget.attrs.update({'class': 'cyber-input'})
        
        # Llenar los campos bloqueados con la info actual
        if self.instance and self.instance.pk:
            self.fields['telefono'].initial = self.instance.telefono
        if user:
            self.fields['email'].initial = user.email
            self.fields['email'].widget.attrs.update({'class': 'cyber-input', 'style': 'opacity: 0.6; cursor: not-allowed;'})
            self.fields['telefono'].widget.attrs.update({'class': 'cyber-input', 'style': 'opacity: 0.6; cursor: not-allowed;'})