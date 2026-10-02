import datetime

from django.core.exceptions import ValidationError

import pytest

from apps.challenge import (
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_REPLACEMENT,
)
from apps.challenge.models import (
    AnnualStateSetting,
    HelperSessionAvailability,
    Season,
    Session,
)
from apps.challenge.models.registration import Registration
from apps.common import (
    DV_SEASON_STATE_ARCHIVED,
    DV_SEASON_STATE_FINISHED,
    DV_SEASON_STATE_OPEN,
    DV_SEASON_STATE_PLANNING,
    DV_SEASON_STATE_RUNNING,
)
from apps.orga.tests.factories import OrganizationFactory
from apps.user import FORMATION_M2
from apps.user.tests.factories import UserFactory

from .factories import (
    QualificationActivityFactory,
    QualificationFactory,
    SeasonFactory,
    SessionFactory,
)

DAY = datetime.date(2030, 3, 4)


@pytest.fixture
def session(db):
    return SessionFactory(orga__address_canton="VD", day=DAY, begin=datetime.time(9))


def drop_availabilities(session):
    HelperSessionAvailability.objects.filter(session=session).delete()


def test_qualif_actor_without_availability_is_incoherent(session):
    quali = QualificationFactory(session=session, actor=UserFactory())
    drop_availabilities(session)
    assert quali.has_availability_incoherences is True


def test_qualif_leader_without_availability_is_incoherent(session):
    quali = QualificationFactory(session=session, leader=UserFactory())
    drop_availabilities(session)
    assert quali.has_availability_incoherences is True


def test_qualif_helper_without_availability_is_incoherent(session):
    quali = QualificationFactory(session=session, helpers=[UserFactory()])
    drop_availabilities(session)
    assert quali.has_availability_incoherences is True


def test_qualif_coherent_availabilities(session):
    quali = QualificationFactory(
        session=session,
        leader=UserFactory(),
        actor=UserFactory(),
        helpers=[UserFactory()],
    )
    assert quali.has_availability_incoherences is False
    assert session.has_availability_incoherences is False


def test_fix_availability_incoherences_removes_unavailable_staff(session):
    keep = UserFactory()
    quali = QualificationFactory(
        session=session,
        leader=UserFactory(),
        actor=UserFactory(),
        helpers=[UserFactory(), keep],
    )
    HelperSessionAvailability.objects.filter(session=session).exclude(
        helper=keep
    ).delete()

    quali.fix_availability_incoherences()

    assert quali.leader is None
    assert quali.actor is None
    assert list(quali.helpers.all()) == [keep]


def test_user_errors_lists_missing_data(session):
    quali = QualificationFactory(
        session=session, class_teacher_fullname="", n_participants=None
    )
    errors = quali.user_errors(UserFactory())
    for label in [
        "Enseignant·e",
        "Nombre de participant·es",
        "Moniteur·trice·s",
        "Intervenant·e",
        "Postes",
    ]:
        assert label in errors


def test_user_errors_reports_incoherences(session):
    quali = QualificationFactory(session=session, leader=UserFactory())
    drop_availabilities(session)
    assert "Incohérences de dispos" in quali.user_errors(UserFactory())


@pytest.mark.xfail(
    strict=True,
    reason="Qualification.errors calls user_errors(None); when the orga has no "
    "coordinator, None == None makes it skip staff/activity checks",
)
def test_errors_without_coordinator_reports_missing_staff(session):
    quali = QualificationFactory(session=session)
    assert "Moniteur·trice·s" in quali.errors


def test_user_errors_for_coordinator_only_checks_class_data(session):
    coordinator = UserFactory()
    session.orga.coordinator = coordinator
    session.orga.save()
    quali = QualificationFactory(
        session=session,
        class_teacher_fullname="Prof",
        class_teacher_natel="+41791234567",
        n_participants=10,
    )
    assert not quali.user_errors(coordinator)


def test_session_has_availability_incoherences(session):
    QualificationFactory(session=session, leader=UserFactory())
    drop_availabilities(session)
    assert session.has_availability_incoherences is True


def test_session_errors_without_qualifs(session):
    assert "Pas de Qualifs" in session.errors


def test_session_errors_flags_bad_qualif(session):
    QualificationFactory(session=session, name="Classe X")
    assert "Qualif’ Classe X" in session.errors


def test_session_start_and_end_datetime(session):
    assert session.start_datetime == datetime.datetime(2030, 3, 4, 9)
    assert session.end_datetime == datetime.datetime(2030, 3, 4, 12)


def test_session_start_datetime_without_begin():
    session = Session(day=DAY)
    assert session.start_datetime == datetime.datetime(2030, 3, 4, 0, 0)


@pytest.mark.parametrize("plan,expected", [("A", "Programme déluge"), ("", "")])
def test_session_fallback(plan, expected):
    assert str(Session(fallback_plan=plan).fallback) == expected


def make_chosen(session, chosen_as, formation="M1", actor_activity=None):
    user = UserFactory()
    user.profile.formation = formation
    user.profile.save()
    if actor_activity:
        user.profile.actor_for.add(actor_activity)
    HelperSessionAvailability.objects.create(
        session=session, helper=user, availability="y", chosen_as=chosen_as
    )
    return user


def test_session_chosen_helpers_actors(session):
    m1 = make_chosen(session, CHOSEN_AS_HELPER)
    m2 = make_chosen(session, CHOSEN_AS_LEADER, formation=FORMATION_M2)
    make_chosen(session, CHOSEN_AS_REPLACEMENT)
    actor = make_chosen(
        session,
        CHOSEN_AS_ACTOR,
        formation="",
        actor_activity=QualificationActivityFactory(category="C"),
    )
    make_chosen(session, CHOSEN_AS_ACTOR, formation="")

    assert [a.helper for a in session.chosen_helpers()] == [m2, m1]
    assert [a.helper for a in session.chosen_helpers_M2()] == [m2]
    assert [a.helper for a in session.chosen_actors()] == [actor]


def test_session_helper_and_actor_needs(session):
    QualificationFactory(session=session, n_helpers=3)
    QualificationFactory(session=session, n_helpers=1)
    assert session.helper_needs() == [0, 2, 2]
    assert session.actor_needs() == 2


def test_session_user_assignment(session):
    leader, helper, actor, other = UserFactory.create_batch(4)
    QualificationFactory(session=session, leader=leader, actor=actor, helpers=[helper])

    assert session.user_assignment(leader) == CHOSEN_AS_LEADER
    assert session.user_assignment(helper) == CHOSEN_AS_HELPER
    assert session.user_assignment(actor) == CHOSEN_AS_ACTOR
    assert session.user_assignment(other) is None


def test_helpers_time_with_default():
    assert Session(helpers_time=datetime.time(8, 15)).helpers_time_with_default() == (
        datetime.time(8, 15)
    )
    assert Session(begin=datetime.time(9, 30)).helpers_time_with_default() == (
        "<em>8h30</em>"
    )
    assert Session().helpers_time_with_default() == ""


def test_session_city_prefers_session_address(session):
    session.address_city = "Morges"
    assert session.city == "Morges"


def test_session_short(session):
    session.orga.name = "École"
    assert session.short == "École 4.03@9:00"


def test_session_clean_rejects_same_half_day(session):
    duplicate = Session(orga=session.orga, day=DAY, begin=datetime.time(10))
    with pytest.raises(ValidationError) as exc:
        duplicate.clean()
    assert "day" in exc.value.message_dict


def test_session_clean_accepts_other_half_day(session):
    Session(orga=session.orga, day=DAY, begin=datetime.time(14)).clean()


@pytest.mark.parametrize(
    "state,expected",
    [
        (DV_SEASON_STATE_PLANNING, "warning"),
        (DV_SEASON_STATE_OPEN, "success"),
        (DV_SEASON_STATE_RUNNING, "warning"),
        (DV_SEASON_STATE_FINISHED, "default disabled"),
        (DV_SEASON_STATE_ARCHIVED, "default disabled"),
        (99, "default"),
    ],
)
def test_season_state_class(state, expected):
    assert Season(state=state).state_class == expected


def test_season_state_icon_empty_for_unknown_state():
    season = Season(state=99)
    season.state_full = "?"
    assert season.state_icon == ""


def test_season_full_legacy_spring():
    season = Season(year=2019, month_start=1, n_months=7)
    assert season.season_full == "Printemps 2019"


def test_season_full_legacy_autumn():
    season = Season(year=2019, month_start=8, n_months=5)
    assert season.season_full == "Automne 2019"


def test_season_has_availability_incoherences(db):
    season = SeasonFactory(year=2030, month_start=1, n_months=6, cantons=["VD"])
    session = SessionFactory(orga__address_canton="VD", day=DAY)
    QualificationFactory(session=session, leader=UserFactory())
    assert season.has_availability_incoherences is False

    drop_availabilities(session)
    season = Season.objects.get(pk=season.pk)
    assert season.has_availability_incoherences is True


def test_registration_clean_rejects_unmanaged_organization(db):
    registration = Registration(
        coordinator=UserFactory(),
        organization=OrganizationFactory(),
        date=DAY,
    )
    with pytest.raises(ValidationError) as exc:
        registration.clean()
    assert "organization" in exc.value.message_dict


def test_annual_state_setting_str():
    setting = AnnualStateSetting(
        canton="VD", year=2030, cost_per_bike=10, cost_per_participant=2
    )
    assert str(setting) == "2030: VD vélos: 10 participants: 2"
