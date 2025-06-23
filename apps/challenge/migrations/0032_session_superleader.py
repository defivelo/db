from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("challenge", "0031_auto_20161013_1600"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="superleader",
            field=models.ForeignKey(
                blank=True,
                verbose_name="Moniteur +",
                null=True,
                related_name="sess_monplus",
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
            ),
        ),
    ]
