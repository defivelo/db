# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_userprofile_formation'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='social_security',
            field=models.CharField(blank=True, max_length=16),
        ),
    ]
