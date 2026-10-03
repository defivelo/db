import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.forms import ValidationError

import pytest
from rolepermissions.roles import assign_role

from apps.challenge.tests.factories import QualificationActivityFactory, SeasonFactory
from apps.common import DV_SEASON_STATE_OPEN, DV_SEASON_STATE_PLANNING
from apps.user.models import (
    BAGSTATUS_GIFT,
    BAGSTATUS_LOAN,
    BAGSTATUS_NONE,
    BAGSTATUS_PAID,
    MARITALSTATUS_MARRIED,
    MARITALSTATUS_UNDEF,
    USERSTATUS_ACTIVE,
    USERSTATUS_ARCHIVE,
    USERSTATUS_DELETED,
    USERSTATUS_INACTIVE,
    USERSTATUS_RESERVE,
    USERSTATUS_UNDEF,
    UserManagedState,
    UserProfile,
)
from apps.user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_existing_manager_excludes_deleted_profiles():
    kept = UserFactory()
    deleted = UserFactory(profile__status=USERSTATUS_DELETED)

    existing = set(UserProfile.objects_existing.all())

    assert kept.profile in existing
    assert deleted.profile not in existing
    assert deleted.profile in set(UserProfile.objects.all())


def test_save_keeps_activity_cantons_when_affiliation_not_listed():
    user = UserFactory(profile__affiliation_canton="VD")
    profile = user.profile
    profile.activity_cantons = ["GE", "NE"]
    profile.save()
    profile.refresh_from_db()

    assert profile.activity_cantons == ["GE", "NE"]


def test_save_removes_affiliation_from_activity_cantons():
    user = UserFactory(profile__affiliation_canton="VD")
    profile = user.profile
    profile.activity_cantons = ["GE", "VD"]
    profile.save()
    profile.refresh_from_db()

    assert profile.activity_cantons == ["GE"]


def test_save_uses_first_challenge_language_as_main_language():
    user = UserFactory(profile__language="")
    profile = user.profile
    profile.languages_challenges = ["de", "it"]
    profile.save()
    profile.refresh_from_db()

    assert profile.language == "de"
    assert profile.languages_challenges == ["it"]


def test_save_keeps_challenge_languages_without_main_language():
    user = UserFactory(profile__language="fr")
    profile = user.profile
    profile.languages_challenges = ["de"]
    profile.save()
    profile.refresh_from_db()

    assert profile.language == "fr"
    assert profile.languages_challenges == ["de"]


def test_set_statemanager_for_keeps_existing_and_removes_others():
    user = UserFactory()
    UserManagedState.objects.create(user=user, canton="VD")
    UserManagedState.objects.create(user=user, canton="GE")

    user.profile.set_statemanager_for(["VD", "NE"])

    assert set(user.managedstates.values_list("canton", flat=True)) == {"VD", "NE"}


def test_send_credentials_refuses_when_user_can_already_login():
    user = UserFactory()
    user.is_active = True
    user.set_password("secret")
    user.save()

    with pytest.raises(ValidationError):
        user.profile.send_credentials({})


@pytest.mark.parametrize(
    "status,expected",
    [(USERSTATUS_UNDEF, ""), (USERSTATUS_RESERVE, "Réserve")],
)
def test_status_full(status, expected):
    user = UserFactory(profile__status=status)

    assert str(user.profile.status_full) == expected


@pytest.mark.parametrize(
    "status,expected",
    [(MARITALSTATUS_UNDEF, ""), (MARITALSTATUS_MARRIED, "Marié·e")],
)
def test_marital_status_full(status, expected):
    user = UserFactory(profile__marital_status=status)

    assert str(user.profile.marital_status_full) == expected


@pytest.mark.parametrize(
    "status,icon",
    [
        (USERSTATUS_ACTIVE, "star"),
        (USERSTATUS_RESERVE, "star-empty"),
        (USERSTATUS_INACTIVE, "hourglass"),
        (USERSTATUS_ARCHIVE, "folder-close"),
        (USERSTATUS_DELETED, "trash"),
    ],
)
def test_status_icon(status, icon):
    user = UserFactory(profile__status=status)

    assert f"glyphicon-{icon}" in user.profile.status_icon()


def test_status_icon_empty_for_undefined_status():
    user = UserFactory(profile__status=USERSTATUS_UNDEF)

    assert user.profile.status_icon() == ""


@pytest.mark.parametrize(
    "status,css_class",
    [
        (USERSTATUS_UNDEF, "default"),
        (USERSTATUS_ACTIVE, "success"),
        (USERSTATUS_RESERVE, "warning"),
        (USERSTATUS_INACTIVE, "danger"),
        (USERSTATUS_ARCHIVE, "default"),
        (USERSTATUS_DELETED, "default disabled"),
    ],
)
def test_status_class(status, css_class):
    user = UserFactory(profile__status=status)

    assert user.profile.status_class() == css_class


def test_age_before_and_after_birthday():
    birthday_passed = UserFactory(profile__birthdate=datetime.date(1998, 1, 1))
    birthday_tomorrow = UserFactory(profile__birthdate=datetime.date(1998, 2, 28))
    now = datetime.datetime(2028, 2, 27, 12, tzinfo=datetime.timezone.utc)

    with patch("apps.user.models.timezone.now", return_value=now):
        assert birthday_passed.profile.age == 30
        assert birthday_tomorrow.profile.age == 29


def test_iban_nice_groups_by_four():
    user = UserFactory(profile__iban="ch9300762011623852957")

    assert user.profile.iban_nice == "CH93 0076 2011 6238 5295 7"


def test_iban_nice_empty():
    user = UserFactory()

    assert user.profile.iban_nice == ""


def test_actor_icon():
    user = UserFactory()
    assert user.profile.actor_icon() == ""

    activity = QualificationActivityFactory(category="C", name="Rencontre")
    user.profile.actor_for.add(activity)
    profile = UserProfile.objects.get(pk=user.pk)

    assert "glyphicon-sunglasses" in profile.actor_icon()
    assert "Rencontre" in profile.actor_icon()


@pytest.mark.parametrize(
    "bagstatus,icon,full",
    [
        (BAGSTATUS_NONE, "unchecked", ""),
        (BAGSTATUS_LOAN, "new-window", "En prêt"),
        (BAGSTATUS_PAID, "check", "Payé"),
        (BAGSTATUS_GIFT, "check", "Offert"),
    ],
)
def test_bagstatus_icon_and_full(bagstatus, icon, full):
    user = UserFactory(profile__bagstatus=bagstatus)

    assert str(user.profile.bagstatus_full) == full
    assert f"glyphicon-{icon}" in user.profile.bagstatus_icon()


def test_language_verb():
    user = UserFactory(profile__language="de")
    assert user.profile.language_verb

    unknown = UserFactory(profile__language="")
    assert unknown.profile.language_verb == ""


def test_languages_challenges_text():
    user = UserFactory(profile__language="fr", profile__languages_challenges=["de"])
    profile = UserProfile.objects.get(pk=user.pk)

    assert profile.languages_challenges_text == "Allemand"


def test_access_level_for_superuser():
    user = UserFactory(is_active=True, is_superuser=True)
    user.set_password("secret")
    user.save()
    profile = UserProfile.objects.get(pk=user.pk)

    assert str(profile.access_level_text) == "Administra·teur·trice"
    assert "glyphicon-queen" in profile.access_level_icon


def test_access_level_without_login():
    user = UserFactory()

    assert user.profile.access_level_text == ""
    assert user.profile.access_level_icon == ""


def test_get_seasons_raises_without_cantons_when_requested():
    user = UserFactory(profile__formation="")
    profile = UserProfile.objects.get(pk=user.pk)

    with pytest.raises(PermissionDenied):
        profile.get_seasons(raise_without_cantons=True)


def test_get_seasons_returns_none_without_cantons():
    user = UserFactory(profile__formation="")
    profile = UserProfile.objects.get(pk=user.pk)

    assert list(profile.get_seasons()) == []


def test_get_seasons_includes_activity_cantons_and_hides_planning():
    user = UserFactory(
        profile__affiliation_canton="VD", profile__activity_cantons=["GE"]
    )
    open_ge = SeasonFactory(cantons=["GE"], state=DV_SEASON_STATE_OPEN)
    planning_ge = SeasonFactory(cantons=["GE"], state=DV_SEASON_STATE_PLANNING)
    open_ne = SeasonFactory(cantons=["NE"], state=DV_SEASON_STATE_OPEN)
    profile = UserProfile.objects.get(pk=user.pk)

    seasons = set(profile.get_seasons())

    assert open_ge in seasons
    assert planning_ge not in seasons
    assert open_ne not in seasons


def test_user_pre_save_generates_username_and_deactivates():
    user = get_user_model()(email="nousername@example.com", is_active=True)
    user.save()

    assert user.username
    assert user.is_active is False


def test_user_managed_state_str():
    user = UserFactory(first_name="Anne", last_name="Dupont")
    ums = UserManagedState.objects.create(user=user, canton="VD")

    assert str(ums) == "Anne Dupont est chargé·e de projet pour le canton VD"


@pytest.mark.xfail(
    reason="canton_full uses self.address_canton which does not exist on "
    "UserManagedState (apps/user/models.py:668)",
    raises=AttributeError,
    strict=True,
)
def test_user_managed_state_canton_full():
    user = UserFactory()
    ums = UserManagedState.objects.create(user=user, canton="VD")

    assert ums.canton_full


def test_send_mail_skipped_without_email():
    user = UserFactory(email="")

    with patch("apps.user.models.send_mail") as mocked:
        assert user.profile.send_mail("subject", "body") is None

    mocked.assert_not_called()


def test_state_manager_role_is_kept_on_save():
    user = UserFactory(profile__formation="")
    assign_role(user, "state_manager")
    profile = UserProfile.objects.get(pk=user.pk)
    profile.save()

    assert user.groups.filter(name="state_manager").exists()
