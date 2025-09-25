from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenge", "0083_historicalqualification_n_helpers_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="season",
            name="availability_reminder_sent_at",
            field=models.DateTimeField(
                verbose_name="Date d’envoi du rappel de disponibilités",
                null=True,
                blank=True,
            ),
        ),
    ]


