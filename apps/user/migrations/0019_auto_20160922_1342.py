from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0018_auto_20160922_1258'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='activity_cantons',
            field=models.CharField(default='', verbose_name='Défi Vélo mobile', choices=[('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich')], max_length=29),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='affiliation_canton',
            field=models.CharField(verbose_name="Canton d'affiliation", choices=[('', '---------'), ('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich')], max_length=2),
        ),
    ]
