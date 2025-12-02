from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OdontogramaEntrada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_diente', models.CharField(max_length=4)),
                ('estado', models.CharField(choices=[('sano', 'Sano'), ('ortodoncia', 'Ortodoncia / Bracket'), ('restauracion', 'Restauración'), ('observacion', 'Observación')], default='sano', max_length=20)),
                ('nota', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('dentista', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='domain.dentista')),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='odontograma', to='domain.paciente')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
