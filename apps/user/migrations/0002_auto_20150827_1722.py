# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import localflavor.generic.models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='address_canton',
            field=models.CharField(max_length=2, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='address_city',
            field=models.CharField(max_length=64, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='address_no',
            field=models.CharField(max_length=8, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='address_street',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='address_zip',
            field=models.CharField(max_length=4, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='natel',
            field=models.CharField(max_length=12, blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='iban',
            field=localflavor.generic.models.IBANField(max_length=34, blank=True),
        ),
    ]
