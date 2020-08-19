from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0023_auto_20151002_0948'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qualification',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Nom de la classe'),
        ),
    ]
