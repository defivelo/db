from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("name", models.CharField(max_length=255, verbose_name="Nom")),
                ("address_street", models.CharField(max_length=255, blank=True)),
                ("address_no", models.CharField(max_length=8, blank=True)),
                ("address_zip", models.CharField(max_length=4, blank=True)),
                ("address_city", models.CharField(max_length=64, blank=True)),
                ("address_canton", models.CharField(max_length=2, blank=True)),
            ],
            options={
                "verbose_name_plural": "Établissements",
                "verbose_name": "Établissement",
                "ordering": ["name"],
            },
        ),
    ]
