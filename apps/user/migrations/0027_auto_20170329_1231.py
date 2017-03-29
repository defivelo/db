# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0026_auto_20170327_1150'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usermanagedstate',
            name='canton',
            field=models.CharField(verbose_name='Canton', choices=[('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich'), ('VS-OW', 'Haut-Valais')], max_length=5),
        ),
    ]
