# paciente/forms.py

from django import forms
from domain.models import Paciente


class PacientePerfilForm(forms.ModelForm):
    """
    Formulario de edición del perfil del paciente en su panel personal.

    Incluye:
      - Nombre
      - Teléfono
      - Dirección
      - Fecha de nacimiento
      - Imagen (foto de perfil)
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
            "nombre": forms.TextInput(
                attrs={
                    "class": "cyber-input",
                    "placeholder": "Nombre completo",
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "cyber-input",
                    "placeholder": "Teléfono de contacto",
                }
            ),
            "direccion": forms.TextInput(
                attrs={
                    "class": "cyber-input",
                    "placeholder": "Dirección",
                }
            ),
            "fecha_nacimiento": forms.DateInput(
                attrs={
                    "class": "cyber-input",
                    "type": "date",
                }
            ),
            "imagen": forms.FileInput(
                attrs={
                    "class": "cyber-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Asegurar clase CSS base en todos los campos
        for field in self.fields.values():
            clases = field.widget.attrs.get("class", "")
            if "cyber-input" not in clases:
                field.widget.attrs["class"] = (clases + " cyber-input").strip()

        # Ejemplo de campo solo lectura si lo necesitas:
        # self.fields["telefono"].widget.attrs.update({
        #     "readonly": "readonly",
        #     "style": "opacity:0.6; cursor:not-allowed;",
        # })
