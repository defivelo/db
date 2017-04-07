# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import migrations, models

from rolepermissions.verifications import has_role
from rolepermissions.shortcuts import grant_permission, revoke_permission


def add_user_can_resend_creds_to_power_user(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    User = get_user_model()
    for user in User.objects.all():
        if has_role(user, 'power_user'):
            grant_permission(user, 'user_can_resend_credentials')
            user.save()

def remove_user_can_resend_creds_from_power_user(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    User = get_user_model()
    for user in User.objects.all():
        if has_role(user, 'power_user'):
            revoke_permission(user, 'user_can_resend_credentials')
            user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('user', '0027_auto_20170329_1231'),
    ]

    operations = [
        migrations.RunPython(add_user_can_resend_creds_to_power_user,
                             remove_user_can_resend_creds_from_power_user),
    ]
