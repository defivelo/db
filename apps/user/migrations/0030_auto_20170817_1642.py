# Generated by Django 1.11.4 on 2017-08-17 14:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0029_auto_20170814_1552'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='language',
            field=models.CharField(blank=True, choices=[('', '---------'), ('fr', 'French'), ('de', 'German'), ('it', 'Italian'), ('en', 'English')], max_length=7, verbose_name='Langue'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='languages_challenges',
            field=models.CharField(blank=True, choices=[('fr', 'French'), ('de', 'German'), ('it', 'Italian'), ('en', 'English')], max_length=11, verbose_name='Prêt à animer en'),
        ),
    ]
