from django.core import validators
from django.db import migrations, models

from apps.common import DV_SEASON_AUTUMN, DV_SEASON_LAST_SPRING_MONTH, DV_SEASON_SPRING


def season_to_months(apps, schema_editor):
    Season = apps.get_model("challenge", "Season")
    for s in Season.objects.all():
        if s.season == DV_SEASON_SPRING:
            s.month_start = 1
            s.n_months = DV_SEASON_LAST_SPRING_MONTH
        if s.season == DV_SEASON_AUTUMN:
            s.month_start = DV_SEASON_LAST_SPRING_MONTH + 1
            s.n_months = 12 - DV_SEASON_LAST_SPRING_MONTH
        s.save()


def months_to_season(apps, schema_editor):
    Season = apps.get_model("challenge", "Season")
    for s in Season.objects.all():
        # We would loose data by applying this reverse migration.
        s.season = DV_SEASON_AUTUMN
        if s.month_start <= DV_SEASON_LAST_SPRING_MONTH:
            s.season = DV_SEASON_SPRING
        s.save()


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0069_use_u2019_quote_qualif"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalseason",
            name="month_start",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "January"),
                    (2, "February"),
                    (3, "March"),
                    (4, "April"),
                    (5, "May"),
                    (6, "June"),
                    (7, "July"),
                    (8, "August"),
                    (9, "September"),
                    (10, "October"),
                    (11, "November"),
                    (12, "December"),
                ],
                null=True,
                verbose_name="Mois de début",
            ),
        ),
        migrations.AddField(
            model_name="historicalseason",
            name="n_months",
            field=models.PositiveSmallIntegerField(
                default=1,
                validators=[
                    validators.MinValueValidator(1),
                    validators.MaxValueValidator(24),
                ],
                verbose_name="Nombre de mois",
            ),
        ),
        migrations.AddField(
            model_name="season",
            name="month_start",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "January"),
                    (2, "February"),
                    (3, "March"),
                    (4, "April"),
                    (5, "May"),
                    (6, "June"),
                    (7, "July"),
                    (8, "August"),
                    (9, "September"),
                    (10, "October"),
                    (11, "November"),
                    (12, "December"),
                ],
                null=True,
                verbose_name="Mois de début",
            ),
        ),
        migrations.AddField(
            model_name="season",
            name="n_months",
            field=models.PositiveSmallIntegerField(
                default=1,
                validators=[
                    validators.MinValueValidator(1),
                    validators.MaxValueValidator(24),
                ],
                verbose_name="Nombre de mois",
            ),
        ),
        migrations.RunPython(season_to_months, months_to_season),
    ]
