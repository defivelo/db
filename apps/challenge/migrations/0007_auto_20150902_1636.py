# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenge', '0006_auto_20150901_1210'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SessionActivity',
            new_name='QualificationActivity',
        ),
        migrations.RenameModel(
            old_name='SessionActivityTranslation',
            new_name='QualificationActivityTranslation',
        ),
        migrations.AddField(
            model_name='qualification',
            name='leader',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='Moniteur 2', null=True, blank=True, related_name='sessions_mon2'),
        ),
        migrations.AlterModelTable(
            name='qualificationactivitytranslation',
            table='challenge_qualificationactivity_translation',
        ),
    ]
