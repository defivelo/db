# Generated by Django 2.2.16 on 2020-10-29 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salary', '0012_add_schwyz'),
    ]

    operations = [
        migrations.AddField(
            model_name='timesheet',
            name='ignore',
            field=models.BooleanField(default=False, verbose_name='Ignorer'),
        ),
    ]