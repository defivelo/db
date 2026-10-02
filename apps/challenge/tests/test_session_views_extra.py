import csv
import datetime
import io
from unittest.mock import Mock

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.urls import reverse

import pytest

from apps.challenge import CHOSEN_AS_HELPER
from apps.challenge.models import HelperSessionAvailability
from apps.challenge.views.mixins import CantonSeasonFormMixin
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import StateManagerAuthClient

from .factories import (
    QualificationActivityFactory,
    QualificationFactory,
    SeasonFactory,
    SessionFactory,
)


@pytest.fixture
def client(db):
    return StateManagerAuthClient()


@pytest.fixture
def season(db):
    return SeasonFactory(year=2030, month_start=1, n_months=6, cantons=["VD"])


@pytest.fixture
def foreign_season(db):
    return SeasonFactory(year=2030, month_start=1, n_months=6, cantons=["GE"])


def detail_url(season, session):
    return reverse("session-detail", kwargs={"seasonpk": season.pk, "pk": session.pk})


def list_url(season):
    return reverse(
        "session-list", kwargs={"seasonpk": season.pk, "year": 2030, "week": 10}
    )


def test_detail_has_previous_and_next_sessions_of_same_orga(client, season):
    first = SessionFactory(orga__address_canton="VD", day=datetime.date(2030, 3, 1))
    middle = SessionFactory(orga=first.orga, day=datetime.date(2030, 3, 2))
    last = SessionFactory(orga=first.orga, day=datetime.date(2030, 3, 3))

    response = client.get(detail_url(season, middle))

    assert response.status_code == 200
    assert response.context["session_previous"] == first
    assert response.context["session_next"] == last


def test_detail_without_chosen_staff_has_no_mailto(client, season):
    session = SessionFactory(orga__address_canton="VD", day=datetime.date(2030, 3, 1))

    response = client.get(detail_url(season, session))

    assert response.context["session_mailtoall"] is None


def test_detail_mailto_lists_chosen_staff(client, season):
    session = SessionFactory(orga__address_canton="VD", day=datetime.date(2030, 3, 1))
    helper = UserFactory(first_name="Jane", last_name="Doe", email="jane@example.com")
    HelperSessionAvailability.objects.create(
        session=session, helper=helper, availability="y", chosen_as=CHOSEN_AS_HELPER
    )
    refused = UserFactory(email="refused@example.com")
    HelperSessionAvailability.objects.create(
        session=session, helper=refused, availability="n", chosen_as=CHOSEN_AS_HELPER
    )

    response = client.get(detail_url(season, session))

    mailto = response.context["session_mailtoall"]
    assert mailto.startswith("mailto:Jane Doe <jane@example.com>?")
    assert "refused@example.com" not in mailto
    assert "subject=" in mailto and "body=" in mailto


def test_detail_for_season_leader_outside_managed_cantons(client, foreign_season):
    foreign_season.leader = client.user
    foreign_season.save()
    session = SessionFactory(orga__address_canton="GE", day=datetime.date(2030, 3, 1))

    response = client.get(detail_url(foreign_season, session))

    assert response.status_code == 200
    assert response.context["season"] == foreign_season


def test_detail_for_mobile_state_manager(client, foreign_season):
    client.user.profile.affiliation_canton = "GE"
    client.user.profile.save()
    session = SessionFactory(orga__address_canton="GE", day=datetime.date(2030, 3, 1))

    response = client.get(detail_url(foreign_season, session))

    assert response.status_code == 200


def test_list_for_season_leader_outside_managed_cantons(client, foreign_season):
    foreign_season.leader = client.user
    foreign_season.save()

    assert client.get(list_url(foreign_season)).status_code == 200


def test_list_for_mobile_state_manager(client, foreign_season):
    client.user.profile.affiliation_canton = "GE"
    client.user.profile.save()

    assert client.get(list_url(foreign_season)).status_code == 200


def test_list_forbidden_for_unrelated_state_manager(client, foreign_season):
    assert client.get(list_url(foreign_season)).status_code == 403


def export_rows(client, season, session):
    url = reverse(
        "session-export",
        kwargs={"seasonpk": season.pk, "pk": session.pk, "format": "csv"},
    )
    response = client.get(url)
    assert response.status_code == 200
    assert "attachment; filename=" in response["Content-Disposition"]
    return list(csv.reader(io.StringIO(response.content.decode("utf-8"))))


def test_export_session_without_qualifications(client, season):
    session = SessionFactory(
        orga__address_canton="VD",
        orga__address_city="Lausanne",
        day=datetime.date(2030, 3, 1),
        begin=datetime.time(9, 0),
        fallback_plan="B",
    )

    rows = export_rows(client, season, session)

    assert len(rows) == 27
    assert rows[0][0] == "Date"
    assert rows[3] == ["Emplacement", "Lausanne"]
    assert rows[4] == ["Heures", "09:00 - 12:00"]
    assert rows[5] == ["Nombre de qualifs", "0"]
    assert rows[7] == ["Mauvais temps", "Annulation"]
    assert all(row[1] == "" for row in rows[14:])


def test_export_session_place_falls_back_to_session_city(client, season):
    session = SessionFactory(
        orga__address_canton="VD",
        day=datetime.date(2030, 3, 1),
        address_city="Morges",
    )

    rows = export_rows(client, season, session)

    assert rows[3] == ["Emplacement", "Morges"]


def test_export_session_with_qualifications(client, season):
    superleader = UserFactory(first_name="Super", last_name="Leader")
    session = SessionFactory(
        orga__address_canton="VD",
        day=datetime.date(2030, 3, 1),
        place="Cour d'école",
        superleader=superleader,
    )
    leader = UserFactory(first_name="Lea", last_name="Der")
    helper = UserFactory(first_name="Hel", last_name="Per")
    actor = UserFactory(first_name="Ac", last_name="Tor")
    activity_c = QualificationActivityFactory(name="Rencontre", category="C")
    QualificationFactory(
        session=session,
        name="Classe A",
        class_teacher_fullname="Prof Un",
        class_teacher_natel="",
        leader=leader,
        helpers=[helper],
        actor=actor,
        activity_C=activity_c,
        n_participants=12,
        n_bikes=5,
    )
    QualificationFactory(
        session=session, name="Classe B", class_teacher_fullname="", n_bikes=3
    )

    rows = export_rows(client, season, session)

    assert len(rows) == 27
    assert all(len(row) == 3 for row in rows)
    assert rows[3][1] == "Cour d'école"
    assert rows[5][1] == "2"
    assert rows[6][1].startswith("Super Leader - ")
    assert rows[11][1] == "8"
    assert rows[14][1:] == ["Classe A", "Classe B"]
    assert rows[15][1].startswith("Prof Un - ")
    assert rows[15][2] == ""
    assert rows[16][1].startswith("Lea Der - ")
    assert rows[16][2] == ""
    assert rows[17][1].startswith("Hel Per - ")
    assert rows[18][1] == ""
    assert rows[19][1] == "12"
    assert rows[24][1] == "Rencontre"
    assert rows[22][1] == ""
    assert rows[25][1].startswith("Ac Tor - ")
    assert rows[25][2] == ""
    assert all(cell == "" for cell in rows[0][2:] + [r[2] for r in rows[:14]])


class DummySeasonView(CantonSeasonFormMixin):
    raise_without_cantons = False

    def __init__(self, user, **kwargs):
        self.kwargs = kwargs
        self.request = RequestFactory().get("/")
        self.request.user = user


def test_season_object_with_invalid_pk_is_none():
    assert DummySeasonView(Mock(), seasonpk="abc").season_object is None
    assert DummySeasonView(Mock()).season_object is None


def test_season_property_without_season_is_none():
    assert DummySeasonView(Mock(), seasonpk="abc").season is None


def test_season_property_unknown_season_raises_value_error(client):
    view = DummySeasonView(client.user, seasonpk="999999")
    with pytest.raises(ValueError):
        view.season


def test_season_property_hidden_for_mobile_without_fetch(client, foreign_season):
    client.user.profile.affiliation_canton = "GE"
    client.user.profile.save()
    view = DummySeasonView(client.user, seasonpk=foreign_season.pk)
    assert view.season is None


def test_season_property_allowed_fetch_for_mobile(client, foreign_season):
    client.user.profile.affiliation_canton = "GE"
    client.user.profile.save()
    view = DummySeasonView(client.user, seasonpk=foreign_season.pk)
    view.allow_season_fetch = True
    assert view.season == foreign_season


def test_season_property_raises_for_unrelated_state_manager(client, foreign_season):
    view = DummySeasonView(client.user, seasonpk=foreign_season.pk)
    with pytest.raises(PermissionDenied):
        view.season


def test_season_property_mobile_with_raise_without_cantons(client, foreign_season):
    client.user.profile.affiliation_canton = "GE"
    client.user.profile.save()
    view = DummySeasonView(client.user, seasonpk=foreign_season.pk)
    view.raise_without_cantons = True
    with pytest.raises(PermissionDenied):
        view.season
