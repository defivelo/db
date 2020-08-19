# Generated by Django 1.11.4 on 2017-08-17 12:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orga', '0003_auto_20161014_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='coordinator_phone',
            field=models.CharField(blank=True, max_length=13, verbose_name='Téléphone'),
        ),
        migrations.AddField(
            model_name='organization',
            name='website',
            field=models.URLField(blank=True, verbose_name='Site web'),
        ),
    ]
