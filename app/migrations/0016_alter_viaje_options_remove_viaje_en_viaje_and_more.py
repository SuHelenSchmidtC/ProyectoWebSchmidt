# Generated by Django 5.1.2 on 2024-11-09 21:46

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_vehiculo_lat_vehiculo_lng'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='viaje',
            options={'verbose_name': 'Viaje', 'verbose_name_plural': 'Viajes'},
        ),
        migrations.RemoveField(
            model_name='viaje',
            name='en_viaje',
        ),
        migrations.AddField(
            model_name='viaje',
            name='apoderado',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.apoderado'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='viaje',
            name='estado_viaje',
            field=models.CharField(choices=[('en_progreso', 'En progreso'), ('finalizado', 'Finalizado'), ('cancelado', 'Cancelado')], default='en_progreso', max_length=50),
        ),
        migrations.AddField(
            model_name='viaje',
            name='fecha_llegada',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='viaje',
            name='fecha_salida',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='viaje',
            name='vehiculo',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.vehiculo'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='viaje',
            name='ubicacion',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
    ]
