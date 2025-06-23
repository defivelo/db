from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orga", "0002_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="comments",
            field=models.TextField(verbose_name="Remarques", blank=True),
        ),
        migrations.AddField(
            model_name="organization",
            name="coordinator_email",
            field=models.EmailField(
                max_length=254, verbose_name="Courriel", blank=True
            ),
        ),
        migrations.AddField(
            model_name="organization",
            name="coordinator_fullname",
            field=models.CharField(
                max_length=512, verbose_name="Coordinateur", blank=True
            ),
        ),
        migrations.AddField(
            model_name="organization",
            name="coordinator_natel",
            field=models.CharField(max_length=13, verbose_name="Natel", blank=True),
        ),
    ]
