# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_auto_20151008_1613'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='actor_for',
            field=models.ForeignKey(verbose_name='Intervenant', related_name='actors', null=True, blank=True, to='challenge.QualificationActivity', on_delete=models.CASCADE),
        ),
    ]
