from __future__ import unicode_literals

import localflavor.generic.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0006_require_contenttypes_0002"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                        related_name="profile",
                        on_delete=models.CASCADE,
                    ),
                ),
                ("iban", localflavor.generic.models.IBANField(max_length=34)),
            ],
        ),
    ]
