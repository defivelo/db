# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0015_auto_20150907_1155'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='session',
            options={'ordering': ['day', 'begin', 'organization__name'], 'verbose_name': 'Session', 'verbose_name_plural': 'Sessions'},
        ),
    ]
