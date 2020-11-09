from django.db import migrations
import multiselectfield.db.fields


def ws_to_vs(apps, schema_editor):
    Season = apps.get_model("challenge", "Season")
    # As of 2020-11-09, there are 3 Seasons with 'WS' (and they're alone as such)
    # As the Orga will move to "VS", these can safely be deleted.

    # Delete the seasons that are only "VS"
    Season.objects.filter(cantons="WS").delete()

    # Alter the cantons' array to set "VS" where it's "WS" (but this will affect no Season)
    for season in Season.objects.all():
        cantons = ["VS" if c == "WS" else c for c in season.cantons]
        season.cantons = cantons
        season.save()


class Migration(migrations.Migration):

    dependencies = [
        ("challenge", "0073_correct_season_state_labels"),
    ]

    operations = [
        migrations.RunPython(ws_to_vs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="historicalseason",
            name="cantons",
            field=multiselectfield.db.fields.MultiSelectField(
                choices=[
                    ("AG", "Aargau"),
                    ("AR", "Appenzell Ausserrhoden"),
                    ("BE", "Berne"),
                    ("BL", "Basel-Land"),
                    ("BS", "Basel-Stadt"),
                    ("FR", "Fribourg"),
                    ("GE", "Geneva"),
                    ("GR", "Graubuenden"),
                    ("JU", "Jura"),
                    ("LU", "Lucerne"),
                    ("NE", "Neuchatel"),
                    ("SG", "St. Gallen"),
                    ("SO", "Solothurn"),
                    ("SZ", "Schwyz"),
                    ("VD", "Vaud"),
                    ("VS", "Valais"),
                    ("ZH", "Zurich"),
                ],
                max_length=50,
                verbose_name="Cantons",
            ),
        ),
        migrations.AlterField(
            model_name="season",
            name="cantons",
            field=multiselectfield.db.fields.MultiSelectField(
                choices=[
                    ("AG", "Aargau"),
                    ("AR", "Appenzell Ausserrhoden"),
                    ("BE", "Berne"),
                    ("BL", "Basel-Land"),
                    ("BS", "Basel-Stadt"),
                    ("FR", "Fribourg"),
                    ("GE", "Geneva"),
                    ("GR", "Graubuenden"),
                    ("JU", "Jura"),
                    ("LU", "Lucerne"),
                    ("NE", "Neuchatel"),
                    ("SG", "St. Gallen"),
                    ("SO", "Solothurn"),
                    ("SZ", "Schwyz"),
                    ("VD", "Vaud"),
                    ("VS", "Valais"),
                    ("ZH", "Zurich"),
                ],
                max_length=50,
                verbose_name="Cantons",
            ),
        ),
    ]
