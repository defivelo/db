# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015-2020 Didier Raboud <me+defivelo@odyx.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from unittest.mock import patch

from django.core.signals import request_finished
from django.test import override_settings

from rolepermissions.checkers import has_role

from apps.challenge.tests.factories import QualificationActivityFactory
from apps.user import FORMATION_M1, FORMATION_M2
from apps.user.tests.factories import UserFactory


def test_str_representations(db):
    user = UserFactory()

    assert str(user) == user.username
    assert str(user.profile) == user.get_full_name()


def test_automatic_collaborator_role_assignment_formation(db):
    user = UserFactory()
    user.profile.formation = FORMATION_M1
    user.profile.save()
    assert has_role(user, "collaborator")

    user.profile.formation = ""
    user.profile.save()
    assert not has_role(user, "collaborator")


def test_automatic_collaborator_role_assignment_actor(db):
    user = UserFactory()
    category_c = QualificationActivityFactory(category="C")
    category_c.save()
    user.profile.formation = ""
    user.profile.actor_for.add(category_c)
    user.profile.save()
    assert has_role(user, "collaborator")

    user.profile.actor_for.clear()
    user.profile.save()
    assert not has_role(user, "collaborator")


def test_automatic_collaborator_role_assignment_both(db):
    user = UserFactory()
    category_c = QualificationActivityFactory(category="C")
    category_c.save()
    user.profile.formation = FORMATION_M2
    user.profile.actor_for.add(category_c)
    user.profile.save()
    assert has_role(user, "collaborator")

    user.profile.actor_for.clear()
    user.profile.save()
    # Still has a formation
    assert has_role(user, "collaborator")

    user.profile.formation = ""
    user.profile.save()
    assert not has_role(user, "collaborator")


@patch("apps.user.signals.send_mail")
@override_settings(PROFILE_CHANGED_NOTIFY_EMAIL="admin@example.com")
@override_settings(DEFAULT_FROM_EMAIL="system@example.com")
def test_userprofile_field_change_signal_iban_change(mock_send_mail, db, settings):
    mock_send_mail.reset_mock()

    user = UserFactory(profile__iban="CH9300762011623852957")

    user.profile.iban = "CH1404835012345678009"
    user.profile.save()

    # Trigger the end of the request to send the email
    request_finished.send(sender=None)

    mock_send_mail.assert_called_once()
    args = mock_send_mail.call_args[0]
    assert "Notification de modification de données utilisateur" in args[0]
    assert (
        f"Les informations suivantes pour l’utilisateur {user.get_full_name()} / {user.pk} ont été modifiées"
        in args[1]
    )
    assert "IBAN: CH93 0076 2011 6238 5295 7 → CH14 0483 5012 3456 7800 9" in args[1]
    assert args[2] == "system@example.com"
    assert args[3] == ["admin@example.com"]


@patch("apps.user.signals.send_mail")
@override_settings(PROFILE_CHANGED_NOTIFY_EMAIL="admin@example.com")
@override_settings(DEFAULT_FROM_EMAIL="system@example.com")
def test_userprofile_field_change_signal_address_changes(mock_send_mail, db, settings):
    mock_send_mail.reset_mock()

    user = UserFactory(
        profile__address_street="Old Street",
        profile__address_no="123",
        profile__address_zip="1000",
        profile__address_city="Old City",
        profile__address_canton="VD",
    )

    user.profile.address_street = "New Street"
    user.profile.address_no = "456"
    user.profile.address_city = "New City"
    user.profile.save()

    # Trigger the end of the request to send the email
    request_finished.send(sender=None)

    mock_send_mail.assert_called_once()
    args = mock_send_mail.call_args[0]
    assert "Notification de modification de données utilisateur" in args[0]
    assert (
        f"Les informations suivantes pour l’utilisateur {user.get_full_name()} / {user.pk} ont été modifiées"
        in args[1]
    )

    # Check that all three address changes are in the email body
    assert "address_street: Old Street → New Street" in args[1]
    assert "address_no: 123 → 456" in args[1]
    assert "address_city: Old City → New City" in args[1]

    assert args[2] == "system@example.com"
    assert args[3] == ["admin@example.com"]


@patch("apps.user.signals.send_mail")
def test_userprofile_field_change_signal_no_changes_when_empty_old_values(
    mock_send_mail, db, settings
):
    mock_send_mail.reset_mock()

    user = UserFactory()
    user.profile.save()

    user.profile.iban = "CH93 0076 2011 6238 5295 7"
    user.profile.address_street = "New Street"
    user.profile.save()

    mock_send_mail.assert_not_called()


@patch("apps.user.signals.send_mail")
def test_userprofile_field_change_signal_no_changes_when_values_same(
    mock_send_mail, db, settings
):
    mock_send_mail.reset_mock()
    user = UserFactory(
        profile__iban="CH93 0076 2011 6238 5295 7",
        profile__address_street="Same Street",
    )

    user.profile.iban = "CH93 0076 2011 6238 5295 7"
    user.profile.address_street = "Same Street"
    user.profile.save()
    mock_send_mail.assert_not_called()


@patch("apps.user.signals.send_mail")
@override_settings(PROFILE_CHANGED_NOTIFY_EMAIL="admin@example.com")
@override_settings(DEFAULT_FROM_EMAIL="system@example.com")
def test_userprofile_unified_post_save_notification_sends_email(
    mock_send_mail, db, settings
):
    """
    Test that when multiple models (user + profile) are changed in a single save, the mail is sent only once.
    """
    mock_send_mail.reset_mock()

    user = UserFactory(
        email="mytest@example.com",
        profile__iban="CH93 0076 2011 6238 5295 7",
        profile__address_street="Same Street",
    )

    user.profile.iban = "CH14 0483 5012 3456 7800 9"
    user.profile.address_street = "Different Street"
    user.email = "changed@example.com"
    user.profile.save()
    user.save()

    # Trigger the end of the request to send the email
    request_finished.send(sender=None)

    mock_send_mail.assert_called_once()
    args = mock_send_mail.call_args[0]
    assert "Notification de modification de données utilisateur" in args[0]
    assert (
        f"Les informations suivantes pour l’utilisateur {user.get_full_name()} / {user.pk} ont été modifiées"
        in args[1]
    )
    assert "IBAN: CH93 0076 2011 6238 5295 7 → CH14 0483 5012 3456 7800 9" in args[1]
    assert "address_street: Same Street → Different Street" in args[1]
    assert "email: mytest@example.com → changed@example.com" in args[1]
