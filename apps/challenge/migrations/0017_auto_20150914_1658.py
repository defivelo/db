from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('challenge', '0016_auto_20150911_1738'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='session',
            name='id',
        ),
        migrations.AddField(
            model_name='session',
            name='address_ptr',
            field=models.OneToOneField(to='common.Address', parent_link=True, auto_created=True, serialize=False, default=1, primary_key=True, on_delete=models.CASCADE),
            preserve_default=False,
        ),
    ]
