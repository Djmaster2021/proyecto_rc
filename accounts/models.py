# accounts/models.py

from django.db import models
from django.contrib.auth.models import User

# Este es el modelo que extiende al User de Django
class PerfilDentista(models.Model):
    # OneToOneField crea una relación uno a uno. Cada Usuario solo puede tener un perfil.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_dentista')
    
    # Aquí van los campos específicos del dentista
    licencia = models.CharField(max_length=100, blank=True)
    especialidad = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"Perfil de {self.user.username}"