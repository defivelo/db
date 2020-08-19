from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenge', '0007_auto_20150902_1636'),
    ]

    operations = [
        migrations.AddField(
            model_name='qualification',
            name='helpers',
            field=models.ManyToManyField(verbose_name='Moniteurs 1', to=settings.AUTH_USER_MODEL, related_name='sessions_mon1', blank=True),
        ),
    ]
