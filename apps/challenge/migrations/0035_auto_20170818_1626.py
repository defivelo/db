# Generated by Django 1.11.4 on 2017-08-18 14:26
from __future__ import unicode_literals

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0034_auto_20170814_1552'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='session',
            options={'ordering': ['day', 'begin', 'orga__name'], 'verbose_name': 'Session', 'verbose_name_plural': 'Sessions'},
        ),
        migrations.AlterField(
            model_name='season',
            name='cantons',
            field=multiselectfield.db.fields.MultiSelectField(choices=[('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich'), ('VS-OW', 'Haut-Valais'), ('AP', 'Appenzell')], max_length=41, verbose_name='Cantons'),
        ),
    ]
