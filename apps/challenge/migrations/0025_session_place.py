# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0024_auto_20151015_0958'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='place',
            field=models.CharField(max_length=512, verbose_name='Lieu de la qualification', blank=True),
        ),
    ]
