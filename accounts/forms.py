# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.db import transaction, IntegrityError # <-- Se importa IntegrityError (buena práctica)
from domain.models import Paciente, Dentista  # Importamos el modelo Paciente y Dentista

# --- 1. IMPORTAMOS LOS VALIDADORES ---
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


# --- 2. DEFINIMOS NUESTRAS REGLAS (VALIDADORES) ---
# (Esta parte estaba correcta, no se modifica)

# Validador para usuario: solo letras y números
username_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9]+$',
    message='El usuario solo puede contener letras y números.'
)

# Validador para nombres/apellidos: solo letras, espacios y acentos
name_validator = RegexValidator(
    regex=r'^[a-zA-Z\sñÑáéíóúÁÉÍÓÚüÜ]+$',
    message='Este campo solo puede contener letras y espacios.'
)

# Validador para teléfono: exactamente 10 números
phone_validator = RegexValidator(
    regex=r'^[0-9]{10}$',
    message='El teléfono debe tener exactamente 10 números (sin espacios ni guiones).'
)


# --- 3. MODIFICAMOS TU FORMULARIO ---
# (Los campos del formulario estaban correctos, no se modifican)

class PacienteRegisterForm(UserCreationForm):
    
    # --- Aplicamos las reglas a los campos ---
    username = forms.CharField(
        label="Usuario",
        max_length=25,  # Regla: Máximo 25
        validators=[username_validator], # Regla: Letras y números
        widget=forms.TextInput(attrs={'placeholder': 'ej. juanperez'})
    )
    first_name = forms.CharField(
        label="Nombre",
        min_length=4, # Regla: Mínimo 15
        max_length=25, # Regla: Máximo 25
        validators=[name_validator], # Regla: Solo letras
        widget=forms.TextInput(attrs={'placeholder': 'ej. Juan Alberto'})
    )
    last_name = forms.CharField(
        label="Apellido",
        min_length=8, # Regla: Mínimo 15
        max_length=25, # Regla: Máximo 25
        validators=[name_validator], # Regla: Solo letras
        widget=forms.TextInput(attrs={'placeholder': 'ej. Pérez Rodríguez'})
    )
    telefono = forms.CharField(
        label="Teléfono",
        validators=[phone_validator], # Regla: 10 números exactos
        widget=forms.TextInput(attrs={'placeholder': 'ej. 3221234567', 'type': 'tel', 'maxlength': '10', 'minlength': '10'})
    )
    email = forms.EmailField(
        label="Correo (opcional)",
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'ej. juan@correo.com'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    @transaction.atomic
    def save(self, commit=True):
        # 1. Guarda el User (sin cambios)
        user = super().save(commit=False)
        user.is_active = True
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data.get('email') 

        if commit:
            user.save()

        # 2. Asigna el grupo (sin cambios)
        try:
            grupo_pacientes = Group.objects.get(name='Pacientes')
            user.groups.add(grupo_pacientes)
        except Group.DoesNotExist:
            pass 

        # --- INICIO DE LA CORRECCIÓN ---
        # 3. Crea el perfil 'Paciente' enlazado
        try:
            dentista_default = Dentista.objects.first()
            if not dentista_default:
                raise forms.ValidationError("No hay dentistas registrados en el sistema.")

            Paciente.objects.create(
                user=user,
                # Usamos los campos del User para poblar el perfil del Paciente
                nombre=f"{user.first_name} {user.last_name}",
                dentista=dentista_default,
                telefono=self.cleaned_data['telefono'], # El teléfono viene de cleaned_data
            )
        except Exception as e:
            # ¡CAMBIO CLAVE!
            # Si algo falla aquí (ej. la BD), @transaction.atomic
            # revertirá la creación del 'user'
            # y este error se mostrará en el formulario.
            raise forms.ValidationError(
                f"No se pudo crear el perfil de paciente. Error: {e}"
            )

            
        return user
