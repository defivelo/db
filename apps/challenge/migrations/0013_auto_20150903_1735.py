from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0012_auto_20150903_1723"),
    ]

    operations = [
        migrations.AddField(
            model_name="qualification",
            name="n_bikes",
            field=models.PositiveSmallIntegerField(
                null=True, verbose_name="Nombre de vélos"
            ),
        ),
        migrations.AddField(
            model_name="qualification",
            name="n_helmets",
            field=models.PositiveSmallIntegerField(
                null=True, verbose_name="Nombre de casques"
            ),
        ),
        migrations.AddField(
            model_name="qualification",
            name="n_participants",
            field=models.PositiveSmallIntegerField(
                null=True, verbose_name="Nombre de participants"
            ),
        ),
    ]
