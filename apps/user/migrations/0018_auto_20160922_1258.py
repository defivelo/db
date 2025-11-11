from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0017_auto_20160922_1135"),
    ]

    operations = [
        migrations.RenameField(
            model_name="userprofile",
            old_name="activity_cantons",
            new_name="affiliation_canton",
        ),
    ]
