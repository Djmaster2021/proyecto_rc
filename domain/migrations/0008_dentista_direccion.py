from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("domain", "0007_penalizacionlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="dentista",
            name="direccion",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
