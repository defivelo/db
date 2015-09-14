# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='address_canton',
            field=models.CharField(max_length=2, blank=True, verbose_name='Canton'),
        ),
        migrations.AlterField(
            model_name='address',
            name='address_city',
            field=models.CharField(max_length=64, blank=True, verbose_name='Ville'),
        ),
        migrations.AlterField(
            model_name='address',
            name='address_no',
            field=models.CharField(max_length=8, blank=True, verbose_name='N°'),
        ),
        migrations.AlterField(
            model_name='address',
            name='address_street',
            field=models.CharField(max_length=255, blank=True, verbose_name='Rue'),
        ),
        migrations.AlterField(
            model_name='address',
            name='address_zip',
            field=models.CharField(max_length=4, blank=True, verbose_name='NPA'),
        ),
    ]
