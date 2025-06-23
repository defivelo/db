from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Address",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                ("address_street", models.CharField(max_length=255, blank=True)),
                ("address_no", models.CharField(max_length=8, blank=True)),
                ("address_zip", models.CharField(max_length=4, blank=True)),
                ("address_city", models.CharField(max_length=64, blank=True)),
                ("address_canton", models.CharField(max_length=2, blank=True)),
            ],
        ),
    ]
