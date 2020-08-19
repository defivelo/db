from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_auto_20150901_1742'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='formation',
            field=models.CharField(verbose_name='Formation', max_length=2, choices=[('', '----------'), ('M1', 'Moniteur 1'), ('M2', 'Moniteur 2')], blank=True),
        ),
    ]
