# Generated by Django 5.1.2 on 2024-11-06 01:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_ruta_paradas'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehiculo',
            name='lat',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vehiculo',
            name='lng',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
    ]
