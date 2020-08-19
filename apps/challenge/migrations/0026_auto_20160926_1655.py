from __future__ import unicode_literals

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0025_session_place'),
    ]

    operations = [
        migrations.AlterField(
            model_name='season',
            name='cantons',
            field=multiselectfield.db.fields.MultiSelectField(choices=[('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich')], verbose_name='Cantons', max_length=32),
        ),
    ]
