# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0003_address_address_additional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='address_canton',
            field=models.CharField(blank=True, verbose_name='Canton', max_length=5),
        ),
    ]
