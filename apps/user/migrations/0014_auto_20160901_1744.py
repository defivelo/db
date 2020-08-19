from __future__ import unicode_literals

from django.db import migrations, models
import localflavor.generic.models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0013_auto_20151015_1824'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='iban',
            field=localflavor.generic.models.IBANField(False, ('AT', 'BE', 'BG', 'CH', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FR', 'GB', 'GI', 'GR', 'HR', 'HU', 'IE', 'IS', 'IT', 'LI', 'LT', 'LU', 'LV', 'MC', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK', 'SM'), blank=True),
        ),
    ]
