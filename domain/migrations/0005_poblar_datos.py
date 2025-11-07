from django.db import migrations

def crear_grupos(apps, schema_editor):
    """
    Crea los grupos de usuarios iniciales: Pacientes, Dentistas, Administradores.
    """
    Group = apps.get_model('auth', 'Group')
    
    # get_or_create es seguro y evita duplicados
    Group.objects.get_or_create(name='Pacientes')
    Group.objects.get_or_create(name='Dentistas')
    Group.objects.get_or_create(name='Administradores')

class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0004_administrador_telefono_alter_administrador_nombre_and_more'),
    ]

    operations = [
        # Le decimos a Django que ejecute nuestra función
        migrations.RunPython(crear_grupos),
    ]