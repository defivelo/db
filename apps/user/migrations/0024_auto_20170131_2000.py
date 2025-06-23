from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0023_userprofile_formation_lastdate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usermanagedstate",
            name="canton",
            field=models.CharField(
                max_length=2,
                verbose_name="Canton",
                choices=[
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
        migrations.AlterField(
            model_name="userprofile",
            name="activity_cantons",
            field=models.CharField(
                max_length=38,
                verbose_name="Défi Vélo mobile",
                choices=[
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
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="affiliation_canton",
            field=models.CharField(
                max_length=2,
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
