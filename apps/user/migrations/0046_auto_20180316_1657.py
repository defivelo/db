# Generated by Django 1.11.11 on 2018-03-16 15:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0045_allow_power_user_to_mark_inactive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='bagstatus',
            field=models.PositiveSmallIntegerField(choices=[(0, '---'), (10, 'En pr\xeat'), (20, 'Pay\xe9'), (30, 'Offert')], default=0, verbose_name='Sac D\xe9fi V\xe9lo'),
        ),
    ]
