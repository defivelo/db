from __future__ import unicode_literals

import localflavor.generic.models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0013_auto_20151015_1824"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="iban",
            field=localflavor.generic.models.IBANField(
                False,
                (
                    "AT",
                    "BE",
                    "BG",
                    "CH",
                    "CY",
                    "CZ",
                    "DE",
                    "DK",
                    "EE",
                    "ES",
                    "FI",
                    "FR",
                    "GB",
                    "GI",
                    "GR",
                    "HR",
                    "HU",
                    "IE",
                    "IS",
                    "IT",
                    "LI",
                    "LT",
                    "LU",
                    "LV",
                    "MC",
                    "MT",
                    "NL",
                    "NO",
                    "PL",
                    "PT",
                    "RO",
                    "SE",
                    "SI",
                    "SK",
                    "SM",
                ),
                blank=True,
            ),
        ),
    ]
