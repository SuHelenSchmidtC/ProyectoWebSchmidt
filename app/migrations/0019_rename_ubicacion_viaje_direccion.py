# Generated by Django 5.1.2 on 2024-11-10 14:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_ruta_apoderados'),
    ]

    operations = [
        migrations.RenameField(
            model_name='viaje',
            old_name='ubicacion',
            new_name='direccion',
        ),
    ]
