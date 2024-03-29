# Generated by Django 2.2.24 on 2022-01-11 17:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('salary', '0014_merge_WS_in_VS'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monthlycantonalvalidation',
            name='canton',
            field=models.CharField(
                choices=[('AG', 'Aargau'), ('AR', 'Appenzell Ausserrhoden'),
                         ('BS', 'Basel-Stadt'), ('BL', 'Basel-Land'), ('BE', 'Berne'),
                         ('FR', 'Fribourg'), ('GE', 'Geneva'), ('GR', 'Graubuenden'),
                         ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'),
                         ('SZ', 'Schwyz'), ('SO', 'Solothurn'), ('SG', 'St. Gallen'),
                         ('VS', 'Valais'), ('VD', 'Vaud'), ('ZG', 'Zug'),
                         ('ZH', 'Zurich')], max_length=2, unique_for_month='date',
                unique_for_year='date', verbose_name='Canton'),
        ),
    ]
