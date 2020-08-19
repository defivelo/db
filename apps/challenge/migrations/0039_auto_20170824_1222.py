# Generated by Django 1.11.4 on 2017-08-24 10:22
from __future__ import unicode_literals

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0038_auto_20170824_1212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='season',
            name='cantons',
            field=multiselectfield.db.fields.MultiSelectField(choices=[('AR', 'Appenzell Ausserrhoden'), ('BE', 'Berne'), ('BS', 'Basel-Stadt'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VD', 'Vaud'), ('VS', 'Valais'), ('VS-OW', 'Haut-Valais'), ('ZH', 'Zurich')], max_length=41, verbose_name='Cantons'),
        ),
    ]
