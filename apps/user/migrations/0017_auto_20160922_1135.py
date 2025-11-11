from __future__ import unicode_literals

from django.db import migrations, models


def takefirstcanton(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    try:
        UserProfile = apps.get_model("user", "UserProfile")
    except Exception:
        return
    db_alias = schema_editor.connection.alias
    for profile in UserProfile.objects.using(db_alias).all():
        if profile.activity_cantons:
            profile.activity_cantons = profile.activity_cantons[0]
            profile.save()


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0016_auto_20160913_1155"),
    ]

    operations = [
        migrations.RunPython(takefirstcanton),
        migrations.AlterField(
            model_name="userprofile",
            name="activity_cantons",
            field=models.CharField(
                choices=[
                    ("BS", "Basel-Stadt"),
                    ("BE", "Berne"),
                    ("FR", "Fribourg"),
                    ("GE", "Geneva"),
                    ("LU", "Lucerne"),
                    ("NE", "Neuchatel"),
                    ("SG", "St. Gallen"),
                    ("VS", "Valais"),
                    ("VD", "Vaud"),
                    ("ZH", "Zurich"),
                ],
                verbose_name="Canton d'affiliation",
                max_length=2,
            ),
        ),
    ]
