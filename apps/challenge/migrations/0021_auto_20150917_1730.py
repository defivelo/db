# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0020_auto_20150917_1710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='helpersessionavailability',
            name='session',
            field=models.ForeignKey(verbose_name='Session', related_name='availability_statuses', to='challenge.Session'),
        ),
    ]
