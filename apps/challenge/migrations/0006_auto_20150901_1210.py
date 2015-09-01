# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0005_auto_20150831_1624'),
    ]

    operations = [
        migrations.CreateModel(
            name='SessionActivity',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('category', models.CharField(max_length=1, verbose_name='Catégorie', blank=True, choices=[('A', 'Vélo dans la rue'), ('B', 'Mécanique'), ('C', 'Rencontre')])),
            ],
            options={
                'verbose_name': 'Poste',
                'verbose_name_plural': 'Postes',
                'ordering': ['category', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='SessionActivityTranslation',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('name', models.CharField(max_length=255, verbose_name='Nom')),
                ('master', models.ForeignKey(to='challenge.SessionActivity', editable=False, related_name='translations', null=True)),
            ],
            options={
                'db_table': 'challenge_sessionactivity_translation',
                'managed': True,
                'db_tablespace': '',
                'verbose_name': 'Poste Translation',
                'default_permissions': (),
            },
        ),
        migrations.AddField(
            model_name='qualification',
            name='activity_A',
            field=models.ForeignKey(to='challenge.SessionActivity', related_name='sessions_A', blank=True, null=True, verbose_name='Vélo dans la rue'),
        ),
        migrations.AddField(
            model_name='qualification',
            name='activity_B',
            field=models.ForeignKey(to='challenge.SessionActivity', related_name='sessions_B', blank=True, null=True, verbose_name='Mécanique'),
        ),
        migrations.AddField(
            model_name='qualification',
            name='activity_C',
            field=models.ForeignKey(to='challenge.SessionActivity', related_name='sessions_C', blank=True, null=True, verbose_name='Rencontre'),
        ),
        migrations.AlterUniqueTogether(
            name='sessionactivitytranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
