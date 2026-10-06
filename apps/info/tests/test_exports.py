import csv
import io
import json
from datetime import date, time

from django.urls import reverse

import pytest

from apps.challenge.tests.factories import (
    QualificationFactory,
    SeasonFactory,
    SessionFactory,
)
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_SPRING
from apps.info.exports import QualifsCalendarExport
from apps.orga.tests.factories import OrganizationFactory
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import (
    CollaboratorAuthClient,
    StateManagerAuthClient,
)

pytestmark = pytest.mark.django_db

YEAR = 2030


def _url(name, season=DV_SEASON_SPRING, fmt=None, year=YEAR):
    kwargs = {"year": year, "dv_season": season}
    if fmt:
        kwargs["format"] = fmt
    return reverse(name, kwargs=kwargs)


@pytest.fixture
def vd_orga():
    return OrganizationFactory(
        name="École VD", abbr="EVD", address_canton="VD", address_city="Lausanne"
    )


@pytest.fixture
def ge_orga():
    return OrganizationFactory(
        name="École GE", abbr="", address_canton="GE", address_city="Genève"
    )


def _get_json(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return json.loads(response.content)


class TestSeasonSessionsPeriod:
    def test_spring_export_contains_only_january_to_july(
        self, power_user_client, vd_orga
    ):
        SessionFactory(orga=vd_orga, day=date(YEAR, 1, 1))
        SessionFactory(orga=vd_orga, day=date(YEAR, 7, 31))
        SessionFactory(orga=vd_orga, day=date(YEAR, 8, 1))
        SessionFactory(orga=vd_orga, day=date(YEAR - 1, 12, 31))
        rows = _get_json(power_user_client, _url("logistics-export", fmt="json"))
        assert sorted(r["Date"] for r in rows) == ["1.01.30", "31.07.30"]

    def test_autumn_export_contains_only_august_to_december(
        self, power_user_client, vd_orga
    ):
        SessionFactory(orga=vd_orga, day=date(YEAR, 7, 31))
        SessionFactory(orga=vd_orga, day=date(YEAR, 8, 1))
        SessionFactory(orga=vd_orga, day=date(YEAR, 12, 31))
        SessionFactory(orga=vd_orga, day=date(YEAR + 1, 1, 1))
        rows = _get_json(
            power_user_client,
            _url("logistics-export", season=DV_SEASON_AUTUMN, fmt="json"),
        )
        assert sorted(r["Date"] for r in rows) == ["1.08.30", "31.12.30"]

    def test_state_manager_only_sees_own_cantons(self, vd_orga, ge_orga):
        client = StateManagerAuthClient()
        SessionFactory(orga=vd_orga, day=date(YEAR, 3, 3))
        SessionFactory(orga=ge_orga, day=date(YEAR, 3, 3))
        rows = _get_json(client, _url("logistics-export", fmt="json"))
        assert [r["Canton"] for r in rows] == ["VD"]


class TestLogisticsExport:
    def test_rows_and_headers(self, power_user_client, vd_orga):
        session = SessionFactory(
            orga=vd_orga,
            day=date(YEAR, 3, 4),
            begin=time(8, 30),
            bikes_concept="Camion",
            bikes_phone="0790000000",
        )
        QualificationFactory(session=session, n_participants=10, n_bikes=3, n_helmets=2)
        QualificationFactory(session=session, n_participants=12, n_bikes=4, n_helmets=1)
        rows = _get_json(power_user_client, _url("logistics-export", fmt="json"))
        assert rows == [
            {
                "Canton": "VD",
                "Établissement": "École VD",
                "Lieu": "Lausanne",
                "Date": "4.03.30",
                "Heure": "8:30",
                "Classes": 2,
                "Participant·e·s": 22,
                "Vélos loués": 7,
                "Casques loués": 3,
                "Logistique vélos": "Camion",
                "N° de contact vélos": "0790000000",
            }
        ]

    def test_csv_export_attachment(self, power_user_client, vd_orga):
        SessionFactory(orga=vd_orga, day=date(YEAR, 3, 4))
        response = power_user_client.get(_url("logistics-export", fmt="csv"))
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/csv")
        disposition = response["Content-Disposition"]
        assert disposition.startswith('attachment; filename="DV-Logistique-Mois-2030-')
        assert disposition.endswith('.csv"')
        reader = csv.reader(io.StringIO(response.content.decode()))
        header = next(reader)
        assert header[0] == "Canton"
        assert len(list(reader)) == 1

    @pytest.mark.parametrize(
        "fmt,content_type",
        [
            (
                "xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            ("ods", "application/vnd.oasis.opendocument.spreadsheet"),
        ],
    )
    def test_binary_formats(self, power_user_client, vd_orga, fmt, content_type):
        SessionFactory(orga=vd_orga, day=date(YEAR, 3, 4))
        response = power_user_client.get(_url("logistics-export", fmt=fmt))
        assert response.status_code == 200
        assert response["Content-Type"].startswith(content_type)
        assert response["Content-Disposition"].endswith(f'.{fmt}"')
        assert response.content

    def test_html_view_links_to_session_when_season_exists(
        self, power_user_client, vd_orga
    ):
        season = SeasonFactory(year=YEAR, month_start=1, n_months=7, cantons=["VD"])
        session = SessionFactory(orga=vd_orga, day=date(YEAR, 3, 4), begin=time(9))
        response = power_user_client.get(_url("logistics"))
        assert response.status_code == 200
        dataset = response.context["dataset"]
        row = dataset[0]
        expected_url = reverse(
            "session-detail", kwargs={"seasonpk": season.pk, "pk": session.pk}
        )
        assert row[1] == vd_orga.abbr_verb
        assert row[3] == f'<a href="{expected_url}">4.03.30</a>'
        assert row[4] == f'<a href="{expected_url}">9:00</a>'
        assert response.context["dataset_title"].startswith(
            "Planification logistique - "
        )
        assert response.context["dataset_title"].endswith(" 2030")

    def test_html_view_without_season_has_no_link(self, power_user_client, ge_orga):
        SessionFactory(orga=ge_orga, day=date(YEAR, 3, 4), begin=time(9))
        response = power_user_client.get(_url("logistics"))
        row = response.context["dataset"][0]
        assert row[1] == "École GE"
        assert row[3] == "4.03.30"
        assert row[4] == "9:00"


class TestSeasonStatsExport:
    def test_per_canton_aggregates(self, power_user_client, vd_orga, ge_orga):
        leader = UserFactory()
        helper = UserFactory()
        actor = UserFactory()
        s1 = SessionFactory(orga=vd_orga, day=date(YEAR, 3, 4))
        s2 = SessionFactory(orga=vd_orga, day=date(YEAR, 3, 5))
        QualificationFactory(
            session=s1,
            n_participants=10,
            n_bikes=2,
            n_helmets=1,
            leader=leader,
            actor=actor,
            helpers=[helper],
        )
        QualificationFactory(
            session=s1, n_participants=5, n_bikes=1, n_helmets=0, leader=leader
        )
        QualificationFactory(
            session=s2, n_participants=7, n_bikes=0, n_helmets=3, leader=helper
        )
        SessionFactory(orga=ge_orga, day=date(YEAR, 4, 1))

        rows = _get_json(power_user_client, _url("season-stats-export", fmt="json"))
        by_canton = {r["Canton"]: r for r in rows}
        assert set(by_canton) == {"VD", "GE"}
        assert by_canton["VD"] == {
            "Canton": "VD",
            "Établissements": 1,
            "Sessions": 2,
            "Qualifs": 3,
            "Nombre d’élèves": 22,
            "Prêts de vélos": 3,
            "Prêts de casques": 4,
            "Nombre de personnes ayant exercé": 3,
            "… comme moniteur·trice·s 2": 2,
            "… comme moniteur·trice·s 1": 1,
            "… comme intervenant·e·s": 1,
        }
        assert by_canton["GE"]["Sessions"] == 1
        assert by_canton["GE"]["Qualifs"] == 0
        assert by_canton["GE"]["Nombre d’élèves"] is None

    def test_canton_without_sessions_is_skipped(self, power_user_client):
        assert (
            _get_json(power_user_client, _url("season-stats-export", fmt="json")) == []
        )

    def test_filename(self, power_user_client):
        response = power_user_client.get(_url("season-stats-export", fmt="csv"))
        assert 'filename="DV-Stats_Mois-2030-' in response["Content-Disposition"]

    def test_html_view_has_dataset_and_title(self, power_user_client, vd_orga):
        SessionFactory(orga=vd_orga, day=date(YEAR, 3, 4))
        response = power_user_client.get(_url("season-stats"))
        assert response.status_code == 200
        assert response.context["dataset"][0][0] == "VD"
        assert response.context["dataset_title"].startswith("Statistiques - ")


class TestQualifsCalendarExport:
    def test_rows_are_weeks(self, power_user_client, vd_orga, ge_orga):
        SessionFactory(orga=vd_orga, day=date(YEAR, 3, 6), begin=time(8, 0))
        SessionFactory(orga=ge_orga, day=date(YEAR, 3, 6), begin=None)
        rows = _get_json(power_user_client, _url("qualifs-calendar-export", fmt="json"))
        assert len(rows) == 1
        week = rows[0]
        assert list(week) == [
            "Semaine",
            "Lundi",
            "Mardi",
            "Mercredi",
            "Jeudi",
            "Vendredi",
            "Samedi",
            "Dimanche",
        ]
        assert week["Semaine"] == date(YEAR, 3, 4).strftime("%W")
        assert week["Lundi"] == "2030-03-04"
        assert week["Dimanche"] == "2030-03-10"
        lines = week["Mercredi"].split("\n")
        assert lines[0] == "2030-03-06"
        assert sorted(lines[1:]) == sorted(["08:00:00 EVD VD", " École GE GE"])

    def test_multiple_weeks(self, power_user_client, vd_orga):
        SessionFactory(orga=vd_orga, day=date(YEAR, 3, 4))
        SessionFactory(orga=vd_orga, day=date(YEAR, 3, 20))
        rows = _get_json(power_user_client, _url("qualifs-calendar-export", fmt="json"))
        assert [r["Lundi"].split("\n")[0] for r in rows] == [
            "2030-03-04",
            "2030-03-11",
            "2030-03-18",
        ]

    def test_filename(self, power_user_client, vd_orga):
        SessionFactory(orga=vd_orga, day=date(YEAR, 3, 4))
        response = power_user_client.get(_url("qualifs-calendar-export", fmt="csv"))
        assert 'filename="DV-Calendar-2030-' in response["Content-Disposition"]

    def test_export_without_sessions_has_headers_only(self, power_user_client):
        response = power_user_client.get(_url("qualifs-calendar-export", fmt="csv"))

        assert response.status_code == 200
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
        assert rows == [
            [
                "Semaine",
                "Lundi",
                "Mardi",
                "Mercredi",
                "Jeudi",
                "Vendredi",
                "Samedi",
                "Dimanche",
            ]
        ]

    @pytest.mark.xfail(
        reason="user_cantons raises LookupError for users without cantons",
        raises=LookupError,
        strict=True,
    )
    def test_collaborator_export(self, vd_orga):
        SessionFactory(orga=vd_orga, day=date(YEAR, 3, 4))
        client = CollaboratorAuthClient()
        client.get(_url("qualifs-calendar-export", fmt="csv"))


def test_calendar_dataset_title():
    assert (
        QualifsCalendarExport().get_dataset_title() == "Calendar export dataset title"
    )
