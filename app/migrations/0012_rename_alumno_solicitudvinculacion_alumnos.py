# Generated by Django 5.1.2 on 2024-10-25 15:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_rename_alumnos_solicitudvinculacion_alumno'),
    ]

    operations = [
        migrations.RenameField(
            model_name='solicitudvinculacion',
            old_name='alumno',
            new_name='alumnos',
        ),
    ]