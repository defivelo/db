from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0014_auto_20160901_1744"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="office_member",
            field=models.BooleanField(default=False, verbose_name="Bureau Défi Vélo"),
        ),
    ]
