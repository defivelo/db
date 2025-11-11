from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("challenge", "0029_auto_20161010_1518"),
    ]

    operations = [
        migrations.AlterField(
            model_name="session",
            name="organization",
            field=models.ForeignKey(
                related_name="sessions",
                to="orga.Organization",
                verbose_name="Établissement",
                default=5,
                on_delete=models.CASCADE,
            ),
            preserve_default=False,
        ),
    ]
