# Generated by Django 5.1.2 on 2024-11-12 00:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_alter_viaje_apoderado'),
    ]

    operations = [
        migrations.AddField(
            model_name='ruta',
            name='dias',
            field=models.JSONField(default=list),
        ),
    ]
