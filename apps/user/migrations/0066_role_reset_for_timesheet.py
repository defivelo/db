from django.contrib.auth import get_user_model
from django.db import migrations

from rolepermissions.checkers import has_role
from rolepermissions.roles import assign_role, clear_roles


def reset_all_roles(apps, schema_editor):
    User = get_user_model()
    for user in User.objects.all():
        for role in ["collaborator", "state_manager", "power_user", "coordinator"]:
            if has_role(user, role):
                clear_roles(user)
                assign_role(user, role)
                continue


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0065_role_reset_for_orga_edit_address"),
    ]

    operations = [
        migrations.RunPython(reset_all_roles, migrations.RunPython.noop),
    ]
