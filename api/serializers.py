# api/serializers.py

from rest_framework import serializers
from domain.models import Servicio  # Solo necesitamos importar el modelo Servicio
from django.contrib.auth import get_user_model
from domain.models import Dentista, Servicio  # Importamos los modelos correctos

User = get_user_model() # Así se obtiene el User en Django
class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ("id", "nombre", "descripcion", "precio", "activo")

# # Serializer para el perfil del dentista
class PerfilDentistaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dentista
        fields = ['licencia', 'especialidad', 'telefono', 'foto_perfil']

# # Serializer para el modelo de Usuario (incluye perfil anidado)
class UserSerializer(serializers.ModelSerializer):
    perfil_dentista = PerfilDentistaSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'perfil_dentista']
        read_only_fields = ['id', 'username']

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop('perfil_dentista', {})
        perfil = instance.perfil_dentista
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        perfil.licencia = perfil_data.get('licencia', perfil.licencia)
        perfil.especialidad = perfil_data.get('especialidad', perfil.especialidad)
        perfil.telefono = perfil_data.get('telefono', perfil.telefono)
        perfil.save()
        return instance