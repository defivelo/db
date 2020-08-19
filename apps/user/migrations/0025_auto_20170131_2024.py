from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0024_auto_20170131_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='affiliation_canton',
            field=models.CharField(choices=[('', '---------'), ('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich'), ('VS-OW', 'Haut-Valais')], verbose_name="Canton d'affiliation", max_length=5),
        ),
    ]
