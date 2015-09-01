# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20150827_1722'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='natel',
            field=models.CharField(max_length=13, blank=True),
        ),
    ]
