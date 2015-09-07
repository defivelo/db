# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0013_auto_20150903_1735'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qualification',
            name='n_bikes',
            field=models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Nombre de vélos'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='n_helmets',
            field=models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Nombre de casques'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='n_participants',
            field=models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Nombre de participants'),
        ),
    ]
