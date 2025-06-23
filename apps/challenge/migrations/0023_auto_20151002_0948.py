from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0022_auto_20150930_1608"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="session",
            name="chosen_staff",
        ),
        migrations.AddField(
            model_name="helpersessionavailability",
            name="chosen",
            field=models.BooleanField(
                verbose_name="Sélectionné pour la session", default=False
            ),
        ),
    ]
