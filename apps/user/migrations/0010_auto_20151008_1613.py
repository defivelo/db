# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_userprofile_address_3'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='activity_cantons',
            field=multiselectfield.db.fields.MultiSelectField(max_length=77, blank=True, verbose_name="Cantons d'affiliation", choices=[('AG', 'Aargau'), ('AI', 'Appenzell Innerrhoden'), ('AR', 'Appenzell Ausserrhoden'), ('BS', 'Basel-Stadt'), ('BL', 'Basel-Land'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('GL', 'Glarus'), ('GR', 'Graubuenden'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('NW', 'Nidwalden'), ('OW', 'Obwalden'), ('SH', 'Schaffhausen'), ('SZ', 'Schwyz'), ('SO', 'Solothurn'), ('SG', 'St. Gallen'), ('TG', 'Thurgau'), ('TI', 'Ticino'), ('UR', 'Uri'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZG', 'Zug'), ('ZH', 'Zurich')]),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='bagstatus',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Statut', choices=[(0, '---------'), (10, 'Actif'), (20, 'Réserve'), (30, 'Inactif'), (30, 'Archive')]),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='bagstatus_updatetime',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='comments',
            field=models.TextField(blank=True, verbose_name='Remarques'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='firstmed_course',
            field=models.BooleanField(default=False, verbose_name='Cours samaritains'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='firstmed_course_comm',
            field=models.CharField(max_length=255, blank=True, verbose_name='Cours samaritains (spécifier)'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='pedagogical_experience',
            field=models.TextField(blank=True, verbose_name='Expérience pédagogique'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='status',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Statut', choices=[(0, '---------'), (10, 'Actif'), (20, 'Réserve'), (30, 'Inactif'), (30, 'Archive')]),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='status_updatetime',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
