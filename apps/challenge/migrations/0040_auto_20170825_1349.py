# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-25 11:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0039_auto_20170824_1222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='place',
            field=models.CharField(blank=True, max_length=512, verbose_name="Lieu de la Qualif'"),
        ),
    ]