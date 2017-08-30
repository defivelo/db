# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-30 13:14
from __future__ import unicode_literals

import multiselectfield.db.fields

from django.db import migrations, models
from memoize import delete_memoized

from defivelo.roles import user_cantons


def vsow_to_hw(apps, schema_editor):
    UserManagedState = apps.get_model('user', 'UserManagedState')
    for ums in UserManagedState.objects.all():
        if ums.canton == 'VS-OW':
            ums.canton = 'WS'
            ums.save()

    UserProfile = apps.get_model('user', 'UserProfile')
    for up in UserProfile.objects.all():
        cantons = ['WS' if c == 'VS-OW' else c for c in up.activity_cantons]
        up.activity_cantons = cantons
        if up.affiliation_canton == 'VS-OW':
            up.affiliation_canton = 'WS'
        up.save()
    delete_memoized(user_cantons)


def hw_to_vsow(apps, schema_editor):
    UserManagedState = apps.get_model('user', 'UserManagedState')
    for ums in UserManagedState.objects.all():
        if ums.canton == 'WS':
            ums.canton = 'VS-OW'
            ums.save()

    UserProfile = apps.get_model('user', 'UserProfile')
    for up in UserProfile.objects.all():
        cantons = ['VS-OW' if c == 'WS' else c for c in up.activity_cantons]
        up.activity_cantons = cantons
        if up.affiliation_canton == 'WS':
            up.affiliation_canton = 'VS-OW'
        up.save()
    delete_memoized(user_cantons)


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0041_auto_20170824_1212'),
    ]

    operations = [
        migrations.RunPython(vsow_to_hw,
                             hw_to_vsow),
        migrations.AlterField(
            model_name='usermanagedstate',
            name='canton',
            field=models.CharField(choices=[('AR', 'Appenzell Ausserrhoden'), ('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich'), ('WS', 'Haut-Valais')], max_length=5, verbose_name='Canton'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='activity_cantons',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('AR', 'Appenzell Ausserrhoden'), ('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich'), ('WS', 'Haut-Valais')], max_length=38, verbose_name='Défi Vélo mobile'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='affiliation_canton',
            field=models.CharField(blank=True, choices=[('', '---------'), ('AR', 'Appenzell Ausserrhoden'), ('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich'), ('WS', 'Haut-Valais')], max_length=5, verbose_name="Canton d'affiliation"),
        ),
    ]
