from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("domain", "0006_servicio_descripcion_ticketsoporte"),
    ]

    operations = [
        migrations.CreateModel(
            name="PenalizacionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("accion", models.CharField(choices=[("ADVERTENCIA", "Advertencia"), ("AUTO_PENALIZAR", "Penalización automática"), ("SUSPENDER", "Suspender cuenta"), ("REACTIVAR", "Reactivar cuenta")], max_length=20)),
                ("motivo", models.TextField(blank=True)),
                ("monto", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("dentista", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="domain.dentista")),
                ("paciente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="domain.paciente")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
