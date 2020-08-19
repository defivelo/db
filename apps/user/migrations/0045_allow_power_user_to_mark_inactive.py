# Generated by Django 1.11.4 on 2017-09-06 06:49
from __future__ import unicode_literals

from django.db import migrations

from django.contrib.auth import get_user_model
from django.db import migrations

from rolepermissions.checkers import has_role
from rolepermissions.permissions import grant_permission, revoke_permission
from rolepermissions.roles import assign_role, clear_roles

def reset_power_roles(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    User = get_user_model()
    for user in User.objects.all():
        if has_role(user, 'power_user'):
            clear_roles(user)
            assign_role(user, 'power_user')

def revoke_user_mark_inactive_from_power_users(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    User = get_user_model()
    for user in User.objects.all():
        if has_role(user, 'power_user'):
            revoke_permission(user, 'user_mark_inactive')
            user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0044_allow_statemanager_to_send_credentials'),
    ]

    operations = [
        migrations.RunPython(reset_power_roles,
                             revoke_user_mark_inactive_from_power_users),
    ]
