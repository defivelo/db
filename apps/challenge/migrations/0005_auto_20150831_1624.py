from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0004_auto_20150831_1529"),
    ]

    operations = [
        migrations.CreateModel(
            name="Qualification",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("name", models.CharField(verbose_name="Nom", max_length=255)),
            ],
            options={
                "ordering": ["session", "created_on", "name"],
                "verbose_name": "Qualification",
                "verbose_name_plural": "Qualifications",
            },
        ),
        migrations.AlterModelOptions(
            name="session",
            options={
                "ordering": ["day", "timeslot__begin", "organization__name"],
                "verbose_name": "Session",
                "verbose_name_plural": "Sessions",
            },
        ),
        migrations.AlterField(
            model_name="session",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                related_name="sessions",
                verbose_name="Établissement",
                to="orga.Organization",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="session",
            name="timeslot",
            field=models.ForeignKey(
                blank=True,
                null=True,
                related_name="sessions",
                verbose_name="Horaire",
                to="challenge.SessionTimeSlot",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="qualification",
            name="session",
            field=models.ForeignKey(
                to="challenge.Session",
                related_name="qualifications",
                on_delete=models.CASCADE,
            ),
        ),
    ]
