from django.db import migrations, models


def ws_to_vs(apps, schema_editor):
    MonthlyCantonalValidation = apps.get_model("salary", "MonthlyCantonalValidation")
    for mcv in MonthlyCantonalValidation.objects.filter(canton="WS"):
        # As of 2020-11-09, there are no _validated_ WS mcvs.
        # Still check if there's a VS one (there will), and delete.
        if MonthlyCantonalValidation.objects.filter(
            canton="VS", date=mcv.date
        ).exists():
            mcv.delete()
        else:
            mcv.canton = "VS"
            mcv.save()


class Migration(migrations.Migration):
    dependencies = [
        ("salary", "0013_add_ignore_to_timesheets"),
    ]

    operations = [
        migrations.RunPython(ws_to_vs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="monthlycantonalvalidation",
            name="canton",
            field=models.CharField(
                choices=[
                    ("AG", "Aargau"),
                    ("AR", "Appenzell Ausserrhoden"),
                    ("BS", "Basel-Stadt"),
                    ("BL", "Basel-Land"),
                    ("BE", "Berne"),
                    ("FR", "Fribourg"),
                    ("GE", "Geneva"),
                    ("GR", "Graubuenden"),
                    ("JU", "Jura"),
                    ("LU", "Lucerne"),
                    ("NE", "Neuchatel"),
                    ("SZ", "Schwyz"),
                    ("SO", "Solothurn"),
                    ("SG", "St. Gallen"),
                    ("VS", "Valais"),
                    ("VD", "Vaud"),
                    ("ZH", "Zurich"),
                ],
                max_length=2,
                unique_for_month="date",
                unique_for_year="date",
                verbose_name="Canton",
            ),
        ),
    ]
