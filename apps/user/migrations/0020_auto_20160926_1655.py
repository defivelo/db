from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0019_auto_20160922_1342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='activity_cantons',
            field=models.CharField(choices=[('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich')], blank=True, verbose_name='Défi Vélo mobile', max_length=32),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='affiliation_canton',
            field=models.CharField(choices=[('', '---------'), ('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich')], verbose_name="Canton d'affiliation", max_length=2),
        ),
    ]
