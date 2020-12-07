from django.db import migrations


def ws_to_vs(apps, schema_editor):
    Address = apps.get_model("common", "Address")
    Address.objects.filter(address_canton="WS").update(address_canton="VS")


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0007_use_u2019_quote"),
    ]

    operations = [
        migrations.RunPython(ws_to_vs, migrations.RunPython.noop),
    ]
