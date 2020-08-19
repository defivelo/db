from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0020_auto_20160926_1655'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='office_member',
        ),
    ]
