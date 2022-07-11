from django.db import migrations, models

from memoize import delete_memoized

from defivelo.roles import user_cantons


def ws_to_vs(apps, schema_editor):
    UserManagedState = apps.get_model("user", "UserManagedState")
    for ums in UserManagedState.objects.filter(canton="WS"):
        if UserManagedState.objects.filter(user=ums.user, canton=ums.canton).exists():
            ums.delete()
        else:
            ums.canton = "VS"
            ums.save()

    UserProfile = apps.get_model("user", "UserProfile")
    for up in UserProfile.objects.all():
        cantons = ["VS" if c == "WS" else c for c in up.activity_cantons]
        up.activity_cantons = cantons
        if up.affiliation_canton == "WS":
            up.affiliation_canton = "VS"
        up.save()
    delete_memoized(user_cantons)


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0063_use_u2019_quote"),
    ]

    operations = [
        migrations.RunPython(ws_to_vs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="usermanagedstate",
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
                verbose_name="Canton",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="activity_cantons",
            field=models.CharField(
                blank=True,
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
                max_length=50,
                verbose_name="Défi Vélo mobile",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="affiliation_canton",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "---------"),
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
                verbose_name="Canton d’affiliation",
            ),
        ),
    ]
