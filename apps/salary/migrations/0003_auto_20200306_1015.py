# Generated by Django 2.2.9 on 2020-03-06 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salary", "0002_timesheet_validated_by"),
    ]

    operations = [
        migrations.RemoveField(model_name="timesheet", name="time_monitor",),
        migrations.AddField(
            model_name="timesheet",
            name="time_helper",
            field=models.FloatField(default=0, verbose_name="Heures moni·teur·trice"),
        ),
        migrations.AlterField(
            model_name="timesheet",
            name="time_actor",
            field=models.FloatField(default=0, verbose_name="Heures intervenant·e"),
        ),
    ]
