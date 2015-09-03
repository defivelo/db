# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0011_auto_20150903_1658'),
    ]

    operations = [
        migrations.AddField(
            model_name='qualification',
            name='class_teacher_fullname',
            field=models.CharField(verbose_name='Enseignant', blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name='qualification',
            name='class_teacher_natel',
            field=models.CharField(verbose_name='Natel enseignant', blank=True, max_length=13),
        ),
    ]
