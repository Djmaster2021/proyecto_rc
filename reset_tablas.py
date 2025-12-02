import os
import django
from django.db import connection

# Configura Django para que el script pueda hablar con la BD
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proyecto_rc.settings")
django.setup()

# Lista de tablas que vamos a reiniciar
tables = [
    "domain_cita", 
    "domain_paciente", 
    "domain_servicio", 
    "domain_dentista",
    "domain_horario", 
    "domain_pago", 
    "domain_comprobantepago",
    "domain_encuestasatisfaccion", 
    "domain_notificacion", 
    "domain_avisodentista"
]

print("🧹 Iniciando limpieza de tablas antiguas...")

with connection.cursor() as cursor:
    # Desactivamos chequeo de llaves foráneas para poder borrar sin errores
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")
            print(f"   - Tabla eliminada: {table}")
        except Exception as e:
            print(f"   ! Error borrando {table}: {e}")
            
    # Borramos el historial de migraciones de 'domain' para que crea que es nuevo
    cursor.execute("DELETE FROM django_migrations WHERE app='domain';")
    
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

print("✨ ¡Listo! Las tablas viejas fueron borradas. Ahora ejecuta migrate.")