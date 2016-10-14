# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0022_auto_20161004_1435'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='formation_lastdate',
            field=models.DateField(verbose_name='Date de la dernière formation', blank=True, null=True),
        ),
    ]
