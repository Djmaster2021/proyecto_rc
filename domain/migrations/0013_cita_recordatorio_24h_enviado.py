from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("domain", "0012_cita_veces_reprogramada"),
    ]

    operations = [
        migrations.AddField(
            model_name="cita",
            name="recordatorio_24h_enviado",
            field=models.BooleanField(default=False),
        ),
    ]
