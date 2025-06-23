from django.db import migrations


def ws_to_vs(apps, schema_editor):
    Season = apps.get_model("challenge", "Season")
    # As of 2020-11-09, there are 3 Seasons with 'WS' (and they're alone as such)
    # As the Orga will move to "VS", these can safely be deleted.
    for season in Season.objects.all():
        if season.cantons == ["WS"]:
            season.delete()
            continue
        # Alter the cantons' array to set "VS" where it's "WS" (but this will affect no Season)
        cantons = ["VS" if c == "WS" else c for c in season.cantons]
        season.cantons = cantons
        season.save()


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0073_correct_season_state_labels"),
    ]

    operations = [
        migrations.RunPython(ws_to_vs, migrations.RunPython.noop),
    ]
