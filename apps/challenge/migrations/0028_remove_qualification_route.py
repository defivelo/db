from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0027_auto_20161010_1310"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="qualification",
            name="route",
        ),
    ]
