# Generated by Django 2.2.9 on 2020-03-06 14:04

from django.contrib.auth import get_user_model
from django.db import migrations

from rolepermissions.checkers import has_role
from rolepermissions.permissions import revoke_permission
from rolepermissions.roles import assign_role


def reset_roles(apps, schema_editor):
    User = get_user_model()
    for user in User.objects.all():
        # Re-assigning roles will sync the default associated permissions
        if has_role(user, "power_user"):
            assign_role(user, "power_user")

        if has_role(user, "state_manager"):
            assign_role(user, "state_manager")


def revoke_perms(apps, schema_editor):
    User = get_user_model()
    for user in User.objects.all():
        if has_role(user, "power_user") or has_role(user, "state_manager"):
            revoke_permission(user, "timesheet_editor")


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0053_allow_power_user_to_crud_settings"),
    ]

    operations = [
        migrations.RunPython(reset_roles, revoke_perms),
    ]
