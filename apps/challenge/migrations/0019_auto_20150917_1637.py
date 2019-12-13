# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenge', '0018_season'),
    ]

    operations = [
        migrations.CreateModel(
            name='HelperSessionAvailability',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('availability', models.CharField(max_length=1, choices=[('y', 'Oui'), ('i', 'Si nécessaire'), ('n', 'Non')], verbose_name='Disponible')),
                ('helper', models.ForeignKey(verbose_name='Moniteur', to=settings.AUTH_USER_MODEL, related_name='availabilities', on_delete=models.CASCADE)),
                ('session', models.ForeignKey(verbose_name='Session', to='challenge.Session', related_name='availabilities', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Disponibilité par session',
                'verbose_name_plural': 'Disponibilités par session',
                'ordering': ['session', 'helper', 'availability'],
            },
        ),
        migrations.AlterModelOptions(
            name='season',
            options={'verbose_name': 'Saison', 'verbose_name_plural': 'Saisons', 'ordering': ['begin', 'end']},
        ),
    ]
