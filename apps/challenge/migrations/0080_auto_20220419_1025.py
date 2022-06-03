# Generated by Django 3.2.13 on 2022-04-19 08:25
from django.db.models import Value, F
from django.db.models.functions import Concat

import apps.common.fields
from django.db import migrations, models


def forward(apps, schema_editor):
    """
    Reformat data for the new FieldType
    """
    Season = apps.get_model('challenge', 'Season')
    Season.objects.update(
        cantons=Concat(Value('{'), F('cantons'), Value('}'))
    )

    HSeason = apps.get_model('challenge', 'HistoricalSeason')
    HSeason.objects.update(
        cantons=Concat(Value('{'), F('cantons'), Value('}'))
    )


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0079_add_zoug'),
    ]

    operations = [
        migrations.RunPython(forward),
        migrations.AlterField(
            model_name='historicalseason',
            name='cantons',
            field=apps.common.fields.ChoiceArrayField(
                base_field=models.CharField(
                    choices=[('AG', 'Aargau'), ('AR', 'Appenzell Ausserrhoden'), ('BE', 'Berne'), ('BL', 'Basel-Land'), ('BS', 'Basel-Stadt'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('GR', 'Graubuenden'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('SO', 'Solothurn'), ('SZ', 'Schwyz'), ('VD', 'Vaud'), ('VS', 'Valais'), ('ZG', 'Zug'), ('ZH', 'Zurich')],
                    max_length=2
                ),
                default=list,
                size=None,
                verbose_name='Cantons',
            ),
        ),
        migrations.AlterField(
            model_name='season',
            name='cantons',
            field=apps.common.fields.ChoiceArrayField(
                base_field=models.CharField(
                    choices=[('AG', 'Aargau'), ('AR', 'Appenzell Ausserrhoden'), ('BE', 'Berne'), ('BL', 'Basel-Land'), ('BS', 'Basel-Stadt'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('GR', 'Graubuenden'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('SO', 'Solothurn'), ('SZ', 'Schwyz'), ('VD', 'Vaud'), ('VS', 'Valais'), ('ZG', 'Zug'), ('ZH', 'Zurich')],
                    max_length=2
                ),
                default=list,
                size=None,
                verbose_name='Cantons'
            ),
        ),
    ]
