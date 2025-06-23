from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0003_session_organization"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="session",
            unique_together=set([("organization", "timeslot", "day")]),
        ),
    ]
