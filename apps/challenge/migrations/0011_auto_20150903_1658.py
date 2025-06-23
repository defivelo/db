from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0010_auto_20150903_1606"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="apples",
            field=models.CharField(verbose_name="Pommes", max_length=512, blank=True),
        ),
        migrations.AddField(
            model_name="session",
            name="fallback_plan",
            field=models.CharField(
                verbose_name="Mauvais temps",
                max_length=1,
                choices=[
                    ("A", "Programme déluge"),
                    ("B", "Annulation"),
                    ("C", "Report …"),
                    ("D", "Autre …"),
                ],
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="helpers_place",
            field=models.CharField(
                verbose_name="Lieu rendez-vous moniteurs", max_length=512, blank=True
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="helpers_time",
            field=models.TimeField(
                verbose_name="Heure rendez-vous moniteurs", null=True, blank=True
            ),
        ),
    ]
