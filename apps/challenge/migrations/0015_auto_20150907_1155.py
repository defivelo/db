from __future__ import unicode_literals

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0014_auto_20150907_1143"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="begin",
            field=models.TimeField(null=True, verbose_name="Début", blank=True),
        ),
        migrations.AddField(
            model_name="session",
            name="duration",
            field=models.DurationField(
                verbose_name="Durée", default=datetime.timedelta(0, 10800)
            ),
        ),
        migrations.AlterUniqueTogether(
            name="session",
            unique_together=set([("organization", "begin", "day")]),
        ),
        migrations.RemoveField(
            model_name="session",
            name="timeslot",
        ),
        migrations.DeleteModel(
            name="SessionTimeSlot",
        ),
    ]
