from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0019_auto_20150917_1637'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='helpersessionavailability',
            unique_together=set([('session', 'helper')]),
        ),
    ]
