# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import migrations, models

from rolepermissions.checkers import has_role
from rolepermissions.permissions import grant_permission, revoke_permission


def add_user_deletions_to_power_users(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    User = get_user_model()
    for user in User.objects.all():
        if (
            has_role(user, 'power_user')
        ) and not user.is_superuser:
            grant_permission(user, 'user_deletions')
            user.save()

def remove_user_deletions_from_power_users(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    User = get_user_model()
    for user in User.objects.all():
        if (
            has_role(user, 'power_user')
        ) and not user.is_superuser:
            revoke_permission(user, 'user_deletions')
            user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('user', '0031_auto_20170818_1145'),
    ]

    operations = [
        migrations.RunPython(add_user_deletions_to_power_users,
                             remove_user_deletions_from_power_users),
    ]
