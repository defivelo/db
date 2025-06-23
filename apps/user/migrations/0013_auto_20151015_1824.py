from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0012_userprofile_birthdate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="bagstatus",
            field=models.PositiveSmallIntegerField(
                verbose_name="Sac Défi Vélo",
                default=0,
                choices=[(0, "---"), (10, "En prêt"), (20, "Payé")],
            ),
        ),
    ]
