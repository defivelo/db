# Generated by Django 2.2.12 on 2020-05-18 01:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orga', '0007_organization_organizator_migrate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='coordinator_email',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='coordinator_fullname',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='coordinator_natel',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='coordinator_phone',
        ),
    ]
