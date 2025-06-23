from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0025_auto_20170131_2024"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="affiliation_canton",
            field=models.CharField(
                blank=True,
                max_length=5,
                verbose_name="Canton d'affiliation",
                choices=[
                    ("", "---------"),
                    ("BS", "Basel-Stadt"),
                    ("BE", "Berne"),
                    ("FR", "Fribourg"),
                    ("GE", "Geneva"),
                    ("JU", "Jura"),
                    ("LU", "Lucerne"),
                    ("NE", "Neuchatel"),
                    ("SG", "St. Gallen"),
                    ("VS", "Valais"),
                    ("VD", "Vaud"),
                    ("ZH", "Zurich"),
                    ("VS-OW", "Haut-Valais"),
                ],
            ),
        ),
    ]
