from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='timeslot',
            field=models.ForeignKey(to='challenge.SessionTimeSlot', blank=True, null=True, related_name='sessions', on_delete=models.CASCADE),
        ),
    ]
