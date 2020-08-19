from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenge', '0008_qualification_helpers'),
    ]

    operations = [
        migrations.AddField(
            model_name='qualification',
            name='actor',
            field=models.ForeignKey(verbose_name='Intervenant', blank=True, null=True, to=settings.AUTH_USER_MODEL, related_name='sessions_actor', on_delete=models.CASCADE),
        ),
    ]
