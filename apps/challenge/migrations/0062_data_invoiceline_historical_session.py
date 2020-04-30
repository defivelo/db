# Generated by Django 2.2.9 on 2020-04-08 12:41

from django.db import migrations


def session_to_historical(apps, schema_editor):
    # We can't import the InvoiceLine model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    InvoiceLine = apps.get_model("challenge", "InvoiceLine")
    HistoricalSession = apps.get_model("challenge", "HistoricalSession")
    for il in InvoiceLine.objects.all():
        hs = (
            HistoricalSession.objects.filter(id=il.session_id)
            .order_by("-history_id")
            .last()
        )
        il.historical_session = hs
        il.save()


def historical_to_session(apps, schema_editor):
    # Don't care, no info lost.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("challenge", "0061_invoiceline_historical_session"),
    ]

    operations = [
        migrations.RunPython(session_to_historical, historical_to_session),
    ]
