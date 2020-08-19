from __future__ import unicode_literals

from django.db import models, migrations
import multiselectfield.db.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenge', '0017_auto_20150914_1658'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('begin', models.DateField(verbose_name='Début')),
                ('end', models.DateField(verbose_name='Fin')),
                ('cantons', multiselectfield.db.fields.MultiSelectField(choices=[('AG', 'Aargau'), ('AI', 'Appenzell Innerrhoden'), ('AR', 'Appenzell Ausserrhoden'), ('BS', 'Basel-Stadt'), ('BL', 'Basel-Land'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('GL', 'Glarus'), ('GR', 'Graubuenden'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('NW', 'Nidwalden'), ('OW', 'Obwalden'), ('SH', 'Schaffhausen'), ('SZ', 'Schwyz'), ('SO', 'Solothurn'), ('SG', 'St. Gallen'), ('TG', 'Thurgau'), ('TI', 'Ticino'), ('UR', 'Uri'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZG', 'Zug'), ('ZH', 'Zurich')], max_length=77, verbose_name='Cantons')),
                ('leader', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, verbose_name='Chargé de projet', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Saison',
                'ordering': ['begin', 'end'],
                'verbose_name': 'Saison',
            },
        ),
    ]
