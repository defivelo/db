# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0008_qualification_helpers'),
        ('user', '0005_userprofile_social_security'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='actor_for',
            field=models.ForeignKey(blank=True, related_name='actors', null=True, to='challenge.QualificationActivity'),
        ),
    ]
