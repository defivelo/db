from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0009_qualification_actor'),
    ]

    operations = [
        migrations.AddField(
            model_name='qualification',
            name='comments',
            field=models.TextField(verbose_name='Remarques', blank=True),
        ),
        migrations.AddField(
            model_name='qualification',
            name='route',
            field=models.CharField(max_length=1, verbose_name='Parcours', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], blank=True),
        ),
        migrations.AddField(
            model_name='session',
            name='comments',
            field=models.TextField(verbose_name='Remarques', blank=True),
        ),
    ]
