# Generated by Django 1.11.16 on 2018-10-19 12:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0050_historicalhelperseasonworkwish_historicalhelpersessionavailability_historicalqualification_historica'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalseason',
            name='cantons',
            field=models.CharField(choices=[('AR', 'Appenzell Ausserrhoden'), ('BE', 'Berne'), ('BS', 'Basel-Stadt'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VD', 'Vaud'), ('VS', 'Valais'), ('WS', 'Haut-Valais'), ('ZH', 'Zurich')], max_length=38, verbose_name='Cantons'),
        ),
    ]
