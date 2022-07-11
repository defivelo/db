from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0032_session_superleader'),
    ]

    operations = [
        migrations.AlterField(
            model_name='season',
            name='cantons',
            field=models.CharField(max_length=38, verbose_name='Cantons', choices=[('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich'), ('VS-OW', 'Haut-Valais')]),
        ),
    ]
