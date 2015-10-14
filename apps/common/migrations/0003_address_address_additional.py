# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_auto_20150914_1707'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='address_additional',
            field=models.CharField(max_length=255, verbose_name="Complément d'adresse", blank=True),
        ),
    ]
