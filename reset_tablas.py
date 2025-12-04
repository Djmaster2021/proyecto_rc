import argparse
import os
import sys

import django
from django.db import connection


def main():
    parser = argparse.ArgumentParser(description="⚠️ Script destructivo: borra tablas del dominio.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Omite la confirmación interactiva y procede con el borrado.",
    )
    args = parser.parse_args()

    if not args.force:
        print("Este script borrará datos (tablas domain_*).")
        confirm = input("Escribe 'ELIMINAR' para continuar: ").strip()
        if confirm != "ELIMINAR":
            print("Operación cancelada.")
            return

    # Configura Django para que el script pueda hablar con la BD
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proyecto_rc.settings")
    django.setup()

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
        "domain_avisodentista",
    ]

    print("🧹 Iniciando limpieza de tablas antiguas...")

    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table};")
                print(f"   - Tabla eliminada: {table}")
            except Exception as e:
                print(f"   ! Error borrando {table}: {e}")

        cursor.execute("DELETE FROM django_migrations WHERE app='domain';")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    print("✨ ¡Listo! Las tablas viejas fueron borradas. Ahora ejecuta migrate.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
