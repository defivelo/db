from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0015_userprofile_office_member"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="status",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "---------"),
                    (10, "Actif"),
                    (20, "Réserve"),
                    (30, "Inactif"),
                    (40, "Archive"),
                ],
                verbose_name="Statut",
                default=0,
            ),
        ),
    ]
