from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0026_auto_20160926_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='season',
            name='leader',
            field=models.ForeignKey(verbose_name='Chargé de projet', default=3, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=False,
        ),
    ]
