import datetime

import pytest
from rolepermissions.roles import assign_role

from apps.challenge import (
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_LEGACY,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
)
from apps.challenge.models import HelperSessionAvailability
from apps.challenge.models.availability import HelperSeasonWorkWish
from apps.challenge.utils import (
    GeneralSeason,
    get_cantons_for_seasons,
    get_users_roles_for_session,
    is_morning,
    seasons_in_scope_for_user,
)
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_SPRING
from apps.user.tests.factories import UserFactory

from .factories import QualificationFactory, SeasonFactory, SessionFactory


@pytest.fixture
def session(db):
    return SessionFactory(orga__address_canton="VD", day=datetime.date(2030, 3, 4))


def set_chosen(session, user, chosen_as):
    HelperSessionAvailability.objects.update_or_create(
        session=session,
        helper=user,
        defaults={"availability": "y", "chosen_as": chosen_as},
    )


def test_roles_from_qualification_assignments(session):
    leader, helper, actor, nobody = UserFactory.create_batch(4)
    QualificationFactory(session=session, leader=leader, actor=actor, helpers=[helper])

    roles = get_users_roles_for_session([leader, helper, actor, nobody], session)

    assert roles == {leader: "M2", helper: "M1", actor: "Int.", nobody: ""}


@pytest.mark.parametrize(
    "chosen_as,expected",
    [
        (CHOSEN_AS_LEADER, "M2"),
        (CHOSEN_AS_HELPER, "M1"),
        (CHOSEN_AS_ACTOR, "Int."),
        (CHOSEN_AS_REPLACEMENT, "S"),
        (CHOSEN_AS_LEGACY, "×"),
    ],
)
def test_roles_from_availability_only(session, chosen_as, expected):
    QualificationFactory(session=session)
    user = UserFactory()
    set_chosen(session, user, chosen_as)

    assert get_users_roles_for_session([user], session) == {user: expected}


def test_roles_ignore_not_chosen_availability(session):
    user = UserFactory()
    set_chosen(session, user, CHOSEN_AS_NOT)

    assert get_users_roles_for_session([user], session) == {user: ""}


def test_roles_superleader_alone(session):
    user = UserFactory()
    session.superleader = user
    session.save()

    assert get_users_roles_for_session([user], session) == {user: "M+"}


def test_roles_superleader_combined_with_other_role(session):
    user = UserFactory()
    QualificationFactory(session=session, leader=user)
    session.superleader = user
    session.save()

    assert get_users_roles_for_session([user], session) == {user: "M2 / M+"}


@pytest.mark.parametrize(
    "begin,expected",
    [
        (datetime.time(8, 30), True),
        (datetime.time(12, 0), True),
        (datetime.time(12, 1), False),
        (datetime.time(13, 30), False),
    ],
)
def test_is_morning(begin, expected):
    assert is_morning(begin) is expected


def test_get_cantons_for_seasons_is_unique_and_ordered():
    seasons = [
        SeasonFactory.build(cantons=["VD", "GE"]),
        SeasonFactory.build(cantons=["GE", "FR"]),
    ]
    assert get_cantons_for_seasons(seasons) == ["VD", "GE", "FR"]


def test_general_season_spring_bounds():
    season = SeasonFactory.build(pk=42, cantons=["VD"])
    general = GeneralSeason(year=2024, dv_season=DV_SEASON_SPRING, seasons=[season])

    assert general.pk == 42
    assert general.begin == datetime.date(2024, 1, 1)
    assert general.end == datetime.date(2024, 7, 31)
    assert general.season_full == "Printemps 2024"
    assert general.cantons == ["VD"]


def test_general_season_autumn_bounds_without_seasons():
    general = GeneralSeason(year=2024, dv_season=DV_SEASON_AUTUMN, seasons=[])

    assert general.pk is None
    assert general.begin == datetime.date(2024, 8, 1)
    assert general.end == datetime.date(2024, 12, 31)
    assert general.season_full == "Automne 2024"
    assert general.cantons == []


@pytest.mark.xfail(
    strict=True,
    reason="utils.py:97 tests `elif DV_SEASON_AUTUMN:` (always truthy) "
    "instead of comparing dv_season, so invalid seasons become autumn",
)
def test_general_season_rejects_invalid_dv_season():
    with pytest.raises(Exception):
        GeneralSeason(year=2024, dv_season=99, seasons=[])


def test_general_season_desc():
    season = SeasonFactory.build(cantons=["GE", "VD"])
    general = GeneralSeason(year=2024, dv_season=DV_SEASON_SPRING, seasons=[season])

    assert general.desc() == "Genève, Vaud - Printemps 2024"
    assert '<abbr title="Vaud">VD</abbr>' in general.desc_abbr
    assert general.desc_abbr.endswith(" - Printemps 2024")


@pytest.fixture
def spring_2030(db):
    season = SeasonFactory(year=2030, month_start=1, n_months=7, cantons=["VD"])
    in_scope = SessionFactory(orga__address_canton="VD", day=datetime.date(2030, 3, 4))
    QualificationFactory(session=in_scope)
    no_quali = SessionFactory(orga__address_canton="VD", day=datetime.date(2030, 3, 5))
    other_canton = SessionFactory(
        orga__address_canton="GE", day=datetime.date(2030, 3, 4)
    )
    QualificationFactory(session=other_canton)
    autumn = SessionFactory(orga__address_canton="VD", day=datetime.date(2030, 9, 4))
    QualificationFactory(session=autumn)
    return season, in_scope, no_quali


def test_sessions_with_qualifs_filters_canton_period_and_qualifs(spring_2030):
    season, in_scope, _ = spring_2030
    general = GeneralSeason(year=2030, dv_season=DV_SEASON_SPRING, seasons=[season])

    assert list(general.sessions_with_qualifs) == [in_scope]
    assert general.sessions_with_qualifs is general.sessions_with_qualifs


def test_sessions_with_qualifs_restricted_to_helper(spring_2030):
    season, in_scope, _ = spring_2030
    helper = UserFactory()
    other = SessionFactory(orga__address_canton="VD", day=datetime.date(2030, 4, 1))
    QualificationFactory(session=other, helpers=[helper])
    general = GeneralSeason(
        year=2030,
        dv_season=DV_SEASON_SPRING,
        seasons=[season],
        helper_id=helper.pk,
    )

    assert list(general.sessions_with_qualifs) == [other]
    assert general.cantons == ["VD"]


def test_sessions_with_qualifs_helper_without_assignment_clears_cantons(spring_2030):
    season, _, _ = spring_2030
    helper = UserFactory()
    general = GeneralSeason(
        year=2030,
        dv_season=DV_SEASON_SPRING,
        seasons=[season],
        helper_id=helper.pk,
    )

    assert list(general.sessions_with_qualifs) == []
    assert general.cantons == []


def test_work_wishes_are_summed_across_seasons(db):
    s1 = SeasonFactory(year=2030, month_start=1, n_months=3, cantons=["VD"])
    s2 = SeasonFactory(year=2030, month_start=4, n_months=3, cantons=["GE"])
    unrelated = SeasonFactory(year=2031, cantons=["VD"])
    helper = UserFactory()
    HelperSeasonWorkWish.objects.create(season=s1, helper=helper, amount=2)
    HelperSeasonWorkWish.objects.create(season=s2, helper=helper, amount=3)
    HelperSeasonWorkWish.objects.create(season=unrelated, helper=helper, amount=10)

    general = GeneralSeason(year=2030, dv_season=DV_SEASON_SPRING, seasons=[s1, s2])

    assert list(general.work_wishes) == [{"helper_id": helper.pk, "amount": 5}]


@pytest.fixture
def power_user(db):
    user = UserFactory()
    assign_role(user, "power_user")
    return user


@pytest.fixture
def seasons_2030(db):
    return {
        "spring": SeasonFactory(year=2030, month_start=3, n_months=2, cantons=["VD"]),
        "autumn": SeasonFactory(year=2030, month_start=9, n_months=2, cantons=["VD"]),
        "other_year": SeasonFactory(
            year=2031, month_start=3, n_months=2, cantons=["VD"]
        ),
    }


def test_seasons_in_scope_spring(power_user, seasons_2030):
    qs = seasons_in_scope_for_user(power_user, 2030, DV_SEASON_SPRING)
    assert list(qs) == [seasons_2030["spring"]]


def test_seasons_in_scope_autumn(power_user, seasons_2030):
    qs = seasons_in_scope_for_user(power_user, 2030, DV_SEASON_AUTUMN)
    assert list(qs) == [seasons_2030["autumn"]]


def test_seasons_in_scope_invalid_dv_season_is_empty(power_user, seasons_2030):
    assert not seasons_in_scope_for_user(power_user, 2030, 99).exists()
