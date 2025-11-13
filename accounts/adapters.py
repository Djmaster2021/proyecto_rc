from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from domain.models import Paciente
from django.contrib.auth.models import Group
from django.db import transaction

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def get_login_redirect_url(self, request):
        """
        FUERZA la redirección al dashboard/semáforo siempre.
        Ignora el parámetro ?next= para evitar el bucle de 'Acceso Restringido'.
        """
        return "/accounts/dashboard/"

    @transaction.atomic
    def save_user(self, request, sociallogin, form=None):
        """
        Este método se llama AUTOMÁTICAMENTE cuando un usuario social se registra.
        No necesitamos preguntar si es nuevo, porque si estamos aquí, lo es.
        """
        # 1. Llama al método original para crear el User base de Django
        user = super().save_user(request, sociallogin, form)
        
        # 2. Lógica para crear el perfil de Paciente
        try:
            # Obtenemos datos de Google
            extra_data = sociallogin.account.extra_data
            first_name = extra_data.get('given_name', '')
            last_name = extra_data.get('family_name', '')
            
            # Actualizamos el User con los nombres
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # Creamos el Paciente (Verificamos que no exista ya para evitar errores)
            if not Paciente.objects.filter(user=user).exists():
                Paciente.objects.create(
                    user=user,
                    nombre=f"{user.first_name} {user.last_name}",
                    telefono="" # Se queda vacío por ahora
                )

            # Asignamos el grupo 'Pacientes'
            try:
                grupo_pacientes = Group.objects.get(name='Pacientes')
                user.groups.add(grupo_pacientes)
            except Group.DoesNotExist:
                pass # Si no existe el grupo, seguimos (evita crash)
            
        except Exception as e:
            # Si falla la base de datos, revertimos todo
            raise e 
                
        return user