# Generated by Django 5.1.2 on 2024-11-01 00:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_rename_alumno_solicitudvinculacion_alumnos'),
    ]

    operations = [
        migrations.AddField(
            model_name='alumno',
            name='latitud',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='alumno',
            name='longitud',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
