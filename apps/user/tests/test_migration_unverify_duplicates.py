import datetime
import importlib

from django.utils import timezone

import pytest
from allauth.account.models import EmailAddress

from apps.user.models import USERSTATUS_DELETED
from apps.user.tests.factories import UserFactory

migration = importlib.import_module(
    "apps.user.migrations.0078_unverify_case_duplicate_emails"
)

pytestmark = pytest.mark.django_db


def address(email, primary=True, **user_kwargs):
    user = UserFactory(email=email.lower(), **user_kwargs)
    created = EmailAddress.objects.create(
        user=user, email=email.lower(), primary=primary, verified=False
    )
    # Bypass allauth's lowercasing to recreate legacy mixed-case rows
    EmailAddress.objects.filter(pk=created.pk).update(email=email, verified=True)
    return created


def verified_pks():
    return set(EmailAddress.objects.filter(verified=True).values_list("pk", flat=True))


def test_deleted_account_loses_verification():
    kept = address("jan@example.com", is_active=True)
    deleted = address(
        "Jan@example.com", is_active=False, profile__status=USERSTATUS_DELETED
    )

    assert migration.unverify_case_duplicates(EmailAddress) == [deleted.pk]
    assert verified_pks() == {kept.pk}


def test_primary_address_of_its_owner_wins_over_secondary():
    secondary = address(
        "Max@example.com",
        primary=False,
        is_active=True,
        last_login=timezone.now(),
    )
    secondary.user.email = "other@example.com"
    secondary.user.save()
    kept = address(
        "max@example.com",
        is_active=True,
        last_login=timezone.now() - datetime.timedelta(days=1000),
    )

    assert migration.unverify_case_duplicates(EmailAddress) == [secondary.pk]
    assert verified_pks() == {kept.pk}


def test_most_recent_login_wins_when_otherwise_equal():
    old = address("Ann@example.com", is_active=True, last_login=None)
    recent = address("ann@example.com", is_active=True, last_login=timezone.now())

    migration.unverify_case_duplicates(EmailAddress)

    assert verified_pks() == {recent.pk}
    assert EmailAddress.objects.filter(pk=old.pk).exists()


def test_addresses_without_case_duplicates_are_untouched():
    first = address("one@example.com", is_active=True)
    second = address("two@example.com", is_active=True)
    EmailAddress.objects.create(
        user=UserFactory(), email="ONE@example.com", primary=True, verified=False
    )

    assert migration.unverify_case_duplicates(EmailAddress) == []
    assert verified_pks() == {first.pk, second.pk}
