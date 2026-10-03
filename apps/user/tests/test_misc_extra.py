import queue
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.signals import request_finished
from django.test import override_settings

import pytest
from allauth.account.models import EmailAddress

from apps.user import FORMATION_M1, FORMATION_M2, formation_short
from apps.user import signals as user_signals
from apps.user.admin import EmailAddressAdminForm
from apps.user.export import FirstMedWidget
from apps.user.forms import SimpleUserProfileForm, UserProfileForm
from apps.user.models import UserProfile
from apps.user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_signal_state():
    user_signals._user_changes.clear()
    while not user_signals._userprofile_to_notify.empty():
        user_signals._userprofile_to_notify.get_nowait()
    yield
    user_signals._user_changes.clear()
    while not user_signals._userprofile_to_notify.empty():
        user_signals._userprofile_to_notify.get_nowait()


def test_formation_short():
    assert str(formation_short(FORMATION_M1, real_gettext=True)) == "M1"
    assert str(formation_short(FORMATION_M2, real_gettext=True)) == "M2"
    assert str(formation_short(FORMATION_M2)) == "M2"
    assert formation_short("") == ""


def test_user_email_change_signal_ignores_unsaved_pk():
    User = get_user_model()
    user = User(pk=987654, username="ghost", email="ghost@example.com")

    user_signals.user_email_change_signal(User, user)

    assert 987654 not in user_signals._user_changes


def test_userprofile_field_change_signal_ignores_missing_pk():
    user_signals.userprofile_field_change_signal(UserProfile, UserProfile())

    assert user_signals._user_changes == {}


def test_userprofile_field_change_signal_handles_none_iban():
    user = UserFactory()
    profile = UserProfile.objects.get(pk=user.pk)
    profile.iban = None

    user_signals.userprofile_field_change_signal(UserProfile, profile)

    assert user.pk not in user_signals._user_changes


def test_mark_save_notification_ignores_full_queue():
    user = UserFactory()
    user_signals._user_changes[user.pk] = [
        {"field": "email", "old_value": "a", "new_value": "b"}
    ]

    full_queue = queue.Queue(maxsize=1)
    full_queue.put_nowait("already queued")

    with patch.object(user_signals, "_userprofile_to_notify", full_queue):
        user_signals.userprofile_mark_save_notification(get_user_model(), user)

    assert full_queue.qsize() == 1
    assert full_queue.get_nowait() == "already queued"
    assert user.pk in user_signals._user_changes


class DrainedQueue(queue.Queue):
    """Reports items while actually empty, as when another thread drained it."""

    def empty(self):
        return False


def test_do_userprofile_notification_stops_on_empty_queue():
    with (
        patch.object(user_signals, "_userprofile_to_notify", DrainedQueue()),
        patch("apps.user.signals._send_field_change_notification") as notify,
    ):
        user_signals.do_userprofile_notification()

    notify.assert_not_called()


@override_settings(PROFILE_CHANGED_NOTIFY_EMAIL="admin@example.com")
def test_notification_failure_is_printed(capsys):
    user = UserFactory(email="before@example.com")

    with patch("apps.user.signals.send_mail", side_effect=RuntimeError("smtp down")):
        user.email = "after@example.com"
        user.save()
        request_finished.send(sender=None)

    assert "smtp down" in capsys.readouterr().out
    assert user.pk not in user_signals._user_changes


@override_settings(PROFILE_CHANGED_NOTIFY_EMAIL="")
def test_notification_skipped_without_recipients():
    user = UserFactory()

    with patch("apps.user.signals.send_mail") as mocked:
        user_signals._send_field_change_notification(
            user, [{"field": "email", "old_value": "a", "new_value": "b"}]
        )

    mocked.assert_not_called()


def test_email_admin_form_unsets_other_primary_addresses():
    user = UserFactory()
    old = EmailAddress.objects.create(
        user=user, email="old@example.com", primary=True, verified=True
    )

    form = EmailAddressAdminForm(
        data={
            "user": user.pk,
            "email": "new@example.com",
            "primary": True,
            "verified": True,
        }
    )
    assert form.is_valid(), form.errors
    new = form.save()

    old.refresh_from_db()
    assert old.primary is False
    assert new.primary is True


def test_email_admin_form_keeps_primary_when_not_primary():
    user = UserFactory()
    old = EmailAddress.objects.create(
        user=user, email="old@example.com", primary=True, verified=True
    )

    form = EmailAddressAdminForm(
        data={"user": user.pk, "email": "other@example.com", "verified": True}
    )
    assert form.is_valid(), form.errors
    form.save()

    old.refresh_from_db()
    assert old.primary is True


def test_firstmed_widget_renders_comment():
    user = UserFactory(
        profile__firstmed_course=True, profile__firstmed_course_comm="2020"
    )

    assert FirstMedWidget().render(user.profile) == "Oui - 2020"


def test_firstmed_widget_without_course():
    user = UserFactory(profile__firstmed_course=False)

    assert FirstMedWidget().render(user.profile) == "Non"


def test_simple_profile_form_rejects_duplicate_email():
    UserFactory(email="taken@example.com")
    user = UserFactory(profile__affiliation_canton="", profile__formation="")

    form = SimpleUserProfileForm(
        instance=user,
        allow_email=True,
        data={
            "first_name": "A",
            "last_name": "B",
            "email": "taken@example.com",
            "language": "fr",
        },
    )

    assert not form.is_valid()
    assert "email" in form.errors


@pytest.mark.xfail(
    reason="SimpleUserProfileForm.clean adds an error to 'affiliation_canton' even "
    "when that field is absent (apps/user/forms.py:129)",
    raises=ValueError,
    strict=True,
)
def test_simple_profile_form_monitor_without_affiliation_canton():
    user = UserFactory(profile__affiliation_canton="", profile__formation=FORMATION_M1)

    form = SimpleUserProfileForm(
        instance=user,
        data={"first_name": "A", "last_name": "B", "language": "fr"},
    )

    assert not form.is_valid()


def test_profile_form_disables_affiliation_from_foreign_canton():
    form = UserProfileForm(initial={"affiliation_canton": "GE"}, cantons=["VD"])

    assert form.fields["affiliation_canton"].disabled is True
    keys = [k for k, _ in form.fields["affiliation_canton"].choices]
    assert "GE" in keys
    assert "VD" in keys
    assert "NE" not in keys


def test_profile_form_keeps_affiliation_enabled_in_own_canton():
    form = UserProfileForm(initial={"affiliation_canton": "VD"}, cantons=["VD"])

    assert form.fields["affiliation_canton"].disabled is False
