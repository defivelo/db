from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0028_remove_qualification_route"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="session",
            unique_together=set([]),
        ),
    ]
