# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
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
        label="Nombre completo",
        min_length=4,
        max_length=60,
        validators=[name_validator], # Regla: Solo letras
        widget=forms.TextInput(attrs={'placeholder': 'ej. Juan Pérez'})
    )
    email = forms.EmailField(
        label="Correo",
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'ej. juan@correo.com'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'email')

    @transaction.atomic
    def save(self, commit=True):
        # 1. Guarda el User (sin cambios)
        user = super().save(commit=False)
        user.is_active = True
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = ""  # No solicitamos apellido
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
                nombre=user.first_name,
                dentista=dentista_default,
                telefono="",  # No se solicita en el registro breve
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


class UsernameOrEmailAuthenticationForm(AuthenticationForm):
    """
    Permite iniciar sesión con usuario o correo. Si se detecta un correo,
    se busca el usuario correspondiente y se pasa su username al flujo base.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Usuario o correo electrónico"
        self.fields['username'].widget.attrs.update({
            'placeholder': 'ej. juanperez o correo@dominio.com'
        })

    def clean(self):
        username = self.cleaned_data.get('username')
        if username and '@' in username:
            try:
                user_obj = User.objects.get(email__iexact=username.strip())
                # Sustituimos por el username real antes de la validación base
                self.cleaned_data['username'] = user_obj.get_username()
            except User.DoesNotExist:
                # Si no existe, dejamos que el flujo original genere el error
                pass
        return super().clean()


class UsernameOrEmailPasswordResetForm(PasswordResetForm):
    """
    Permite escribir usuario o correo. Si se ingresa usuario,
    se reemplaza por el correo asociado para que el flujo estándar funcione.
    """
    def clean_email(self):
        identifier = (self.cleaned_data.get("email") or "").strip()
        if not identifier:
            raise ValidationError("Ingresa tu usuario o correo electrónico.")

        if "@" in identifier:
            return identifier

        try:
            user = User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            raise ValidationError("No encontramos una cuenta con esos datos.")

        if not user.email:
            raise ValidationError("Tu cuenta no tiene un correo registrado. Contacta a soporte.")

        # Sustituimos el valor para que el PasswordResetForm use el correo real
        self.cleaned_data["email"] = user.email
        return user.email
