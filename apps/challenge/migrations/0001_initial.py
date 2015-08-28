# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('day', models.DateField(blank=True, verbose_name='Date')),
            ],
            options={
                'verbose_name_plural': 'Sessions',
                'verbose_name': 'Session',
            },
        ),
        migrations.CreateModel(
            name='SessionTimeSlot',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('begin', models.TimeField(verbose_name='Début')),
                ('end', models.TimeField(verbose_name='Fin')),
            ],
            options={
                'verbose_name_plural': 'Horaires pour sessions',
                'ordering': ['begin', 'end'],
                'verbose_name': 'Horaire pour sessions',
            },
        ),
        migrations.AddField(
            model_name='session',
            name='timeslot',
            field=models.ForeignKey(blank=True, related_name='sessions', to='challenge.SessionTimeSlot'),
        ),
    ]
