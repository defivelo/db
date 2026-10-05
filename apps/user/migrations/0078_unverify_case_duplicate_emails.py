"""
allauth's account.0006 lowercases every EmailAddress, which collides with its
`unique_verified_email` constraint when two verified addresses only differ by
case. Keep `verified` on the most legitimate address of each such group and
un-verify the others, so the allauth migrations can run.
"""

from django.db import migrations
from django.db.models import Count
from django.db.models.functions import Lower

USERSTATUS_DELETED = 99


def address_rank(address, lower_email):
    user = address.user
    profile = getattr(user, "profile", None)
    return (
        user.is_active,
        profile is None or profile.status != USERSTATUS_DELETED,
        address.primary,
        (user.email or "").lower() == lower_email,
        user.last_login is not None,
        user.last_login,
        -address.pk,
    )


def unverify_case_duplicates(EmailAddress, using="default"):
    verified = (
        EmailAddress.objects.using(using)
        .filter(verified=True)
        .annotate(lower_email=Lower("email"))
    )
    duplicated = (
        verified.values("lower_email")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
        .values_list("lower_email", flat=True)
    )
    unverified = []
    for lower_email in duplicated:
        addresses = list(
            verified.filter(lower_email=lower_email).select_related(
                "user", "user__profile"
            )
        )
        addresses.sort(key=lambda a: address_rank(a, lower_email), reverse=True)
        unverified += [a.pk for a in addresses[1:]]
    EmailAddress.objects.using(using).filter(pk__in=unverified).update(verified=False)
    return unverified


def forwards(apps, schema_editor):
    unverify_case_duplicates(
        apps.get_model("account", "EmailAddress"), schema_editor.connection.alias
    )


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0077_alter_userprofile_language_and_more"),
        ("account", "0005_emailaddress_idx_upper_email"),
    ]
    run_before = [
        ("account", "0006_emailaddress_lower"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
