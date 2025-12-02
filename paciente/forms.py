# paciente/forms.py

from django import forms
from django.core.validators import RegexValidator
from domain.models import Paciente


class PacienteTelefonoForm(forms.ModelForm):
    """
    Formulario exclusivo para completar perfil (solo teléfono).
    """

    telefono = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='El número de teléfono debe tener exactamente 10 dígitos.',
            )
        ],
        widget=forms.TextInput(
            attrs={
                "id": "telefono",
                "placeholder": "3221234567",
                "class": "cyber-input",
            }
        )
    )

    class Meta:
        model = Paciente
        fields = ["telefono"]


class PacientePerfilForm(forms.ModelForm):
    """
    Formulario para editar perfil dentro del dashboard.
    """
    class Meta:
        model = Paciente
        fields = [
            "nombre",
            "telefono",
            "direccion",
            "fecha_nacimiento",
            "imagen",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "cyber-input"}),
            "telefono": forms.TextInput(attrs={"class": "cyber-input"}),
            "direccion": forms.TextInput(attrs={"class": "cyber-input"}),
            "fecha_nacimiento": forms.DateInput(attrs={"class": "cyber-input", "type": "date"}),
            "imagen": forms.FileInput(attrs={"class": "cyber-input"}),
        }
