import json
from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.challenge.tests.factories import SessionFactory
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_SPRING
from apps.orga.tests.factories import OrganizationFactory
from defivelo.tests.utils import (
    CollaboratorAuthClient,
    CoordinatorAuthClient,
    PowerUserAuthClient,
    StateManagerAuthClient,
)

pytestmark = pytest.mark.django_db

YEAR = 2030


def _url(name, year=YEAR, season=DV_SEASON_SPRING):
    return reverse(name, kwargs={"year": year, "dv_season": season})


class TestPublicViews:
    def test_json_lists_only_future_sessions(self, client):
        orga = OrganizationFactory(name="Orga", abbr="OR", address_canton="VD")
        today = timezone.localdate()
        SessionFactory(orga=orga, day=today - timedelta(days=1))
        future = SessionFactory(orga=orga, day=today + timedelta(days=1))
        response = client.get(reverse("public-json-nextqualifs"))
        data = json.loads(response.content)
        assert len(data["sessions"]) == 1
        session = data["sessions"][0]
        assert session["canton"] == "VD"
        assert session["date"] == future.day.isoformat()
        assert session["orga"] == {"name": "Orga", "abbr": "OR"}

    def test_next_qualifs_can_be_framed(self, client):
        response = client.get(reverse("public-nextqualifs"))
        assert response.status_code == 200
        assert "X-Frame-Options" not in response


class TestSeasonExportsPermissions:
    @pytest.mark.parametrize("name", ["season-exports", "season-stats", "logistics"])
    @pytest.mark.parametrize(
        "client_class,status",
        [
            (PowerUserAuthClient, 200),
            (StateManagerAuthClient, 200),
            (CollaboratorAuthClient, 403),
            (CoordinatorAuthClient, 403),
        ],
    )
    def test_access(self, name, client_class, status):
        assert client_class().get(_url(name)).status_code == status

    def test_season_exports_has_no_dataset(self):
        response = PowerUserAuthClient().get(_url("season-exports"))
        assert "dataset" not in response.context
        assert response.context["submenu_category"] == "statistics-season"
        assert response.context["dataset_exporturl"] == "season-exports-export"


class TestSeasonNavigation:
    def test_spring_navigation(self):
        response = PowerUserAuthClient().get(_url("season-stats"))
        context = response.context
        assert context["export_period"] == {"year": YEAR, "season": DV_SEASON_SPRING}
        assert context["previous_period"] == {
            "year": YEAR - 1,
            "season": DV_SEASON_AUTUMN,
        }
        assert context["next_period"] == {"year": YEAR, "season": DV_SEASON_AUTUMN}
        assert context["nav_url"] == "season-stats"
        assert context["dataset_exporturl"] == "season-stats-export"
        assert context["menu_category"] == "statistics"

    def test_autumn_navigation(self):
        response = PowerUserAuthClient().get(_url("logistics", season=DV_SEASON_AUTUMN))
        context = response.context
        assert context["previous_period"] == {"year": YEAR, "season": DV_SEASON_SPRING}
        assert context["next_period"] == {
            "year": YEAR + 1,
            "season": DV_SEASON_SPRING,
        }

    def test_defaults_to_current_period(self):
        response = PowerUserAuthClient().get(reverse("season-stats"))
        today = date.today()
        expected_season = DV_SEASON_SPRING if today.month <= 7 else DV_SEASON_AUTUMN
        assert response.context["export_period"] == {
            "year": today.year,
            "season": expected_season,
        }


class TestQualifsCalendarView:
    def test_empty_calendar(self):
        response = CollaboratorAuthClient().get(_url("qualifs-calendar"))
        assert response.status_code == 200
        assert "date_sessions" not in response.context
        assert response.context["menu_category"] == "season"
        assert response.context["submenu_category"] == "qualifs-calendar"

    def test_shows_all_cantons_regardless_of_user(self):
        vd = SessionFactory(
            orga=OrganizationFactory(address_canton="VD"), day=date(YEAR, 3, 4)
        )
        ge = SessionFactory(
            orga=OrganizationFactory(address_canton="GE"), day=date(YEAR, 3, 5)
        )
        response = StateManagerAuthClient().get(_url("qualifs-calendar"))
        context = response.context
        assert set(context["legend_cantons"]) == {"VD", "GE"}
        days = context["date_sessions"]
        assert [d["day"] for d in days] == [date(YEAR, 3, d) for d in range(4, 11)]
        assert days[0]["sessions"] == [vd]
        assert days[1]["sessions"] == [ge]

    def test_post_filters_by_canton(self):
        SessionFactory(
            orga=OrganizationFactory(address_canton="VD"), day=date(YEAR, 3, 4)
        )
        ge = SessionFactory(
            orga=OrganizationFactory(address_canton="GE"), day=date(YEAR, 3, 5)
        )
        response = PowerUserAuthClient().post(
            _url("qualifs-calendar"), {"canton": ["GE"]}
        )
        assert response.status_code == 200
        assert set(response.context["legend_cantons"]) == {"GE"}
        sessions = [s for d in response.context["date_sessions"] for s in d["sessions"]]
        assert sessions == [ge]

    def test_post_with_empty_filter_shows_everything(self):
        SessionFactory(
            orga=OrganizationFactory(address_canton="VD"), day=date(YEAR, 3, 4)
        )
        SessionFactory(
            orga=OrganizationFactory(address_canton="GE"), day=date(YEAR, 3, 5)
        )
        response = PowerUserAuthClient().post(_url("qualifs-calendar"), {})
        assert set(response.context["legend_cantons"]) == {"VD", "GE"}

    def test_post_with_invalid_canton_ignores_filter(self):
        SessionFactory(
            orga=OrganizationFactory(address_canton="VD"), day=date(YEAR, 3, 4)
        )
        response = PowerUserAuthClient().post(
            _url("qualifs-calendar"), {"canton": ["XX"]}
        )
        assert set(response.context["legend_cantons"]) == {"VD"}

    def test_filter_without_match_returns_empty_calendar(self):
        SessionFactory(
            orga=OrganizationFactory(address_canton="VD"), day=date(YEAR, 3, 4)
        )
        response = PowerUserAuthClient().post(
            _url("qualifs-calendar"), {"canton": ["GE"]}
        )
        assert "date_sessions" not in response.context
