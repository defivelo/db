# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orga', '0001_initial'),
        ('challenge', '0002_auto_20150828_1405'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='organization',
            field=models.ForeignKey(related_name='sessions', blank=True, null=True, to='orga.Organization', on_delete=models.CASCADE),
        ),
    ]
