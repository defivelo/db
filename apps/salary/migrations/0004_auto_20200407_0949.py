# Generated by Django 2.2.9 on 2020-04-07 07:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salary', '0003_auto_20200306_1015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timesheet',
            name='time_actor',
            field=models.FloatField(default=0, verbose_name='Intervention(s)'),
        ),
    ]
