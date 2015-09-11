# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('user', '0006_userprofile_actor_for'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='address_ptr',
            field=models.ForeignKey(to='common.Address', null=True),
        ),
    ]
