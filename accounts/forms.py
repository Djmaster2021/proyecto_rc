from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.db import transaction
from domain.models import Paciente  # Importamos el modelo Paciente

class PacienteRegisterForm(UserCreationForm):
    # Añadimos solo el campo extra que no está en el User
    telefono = forms.CharField(max_length=15, label="Teléfono")

    class Meta(UserCreationForm.Meta):
        model = User
        # Pedimos los campos que SÍ queremos que el usuario llene
        fields = ('username', 'first_name', 'last_name', 'email')

    @transaction.atomic
    def save(self, commit=True):
        # 1. Guarda el User (username, password, first_name, last_name, email)
        user = super().save(commit=False)
        user.is_active = True
        if commit:
            user.save()

        # 2. Asigna el usuario al grupo 'Pacientes'
        try:
            grupo_pacientes = Group.objects.get(name='Pacientes')
            user.groups.add(grupo_pacientes)
        except Group.DoesNotExist:
            pass # La migración debería prevenir esto

        # 3. Crea el perfil 'Paciente' enlazado
        Paciente.objects.create(
            user=user,
            # Usamos los campos del User para poblar el perfil del Paciente
            nombre=f"{user.first_name} {user.last_name}",
            telefono=self.cleaned_data['telefono'],
        )
        return user