import csv
import datetime
import io
from unittest.mock import patch

from django.test import RequestFactory
from django.urls import reverse

import pytest
from tablib.exceptions import UnsupportedFormat

from apps.salary import BONUS_LEADER, HOURLY_RATE_HELPER, RATE_ACTOR
from apps.salary.views import ExportMonthlyControl, ExportMonthlyTimesheets
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import CollaboratorAuthClient, PowerUserAuthClient

from .factories import TimesheetFactory, ValidatedTimesheetFactory

DAY = datetime.date(2019, 4, 12)


def export_url(name, fmt="csv", year=2019, month=4):
    return reverse(
        f"salary:{name}", kwargs={"year": year, "month": month, "format": fmt}
    )


def parse_csv(response, delimiter=","):
    return list(csv.reader(io.StringIO(response.content.decode()), delimiter=delimiter))


@pytest.fixture
def timesheets(db):
    alice = UserFactory(
        first_name="Alice",
        last_name="Anderson",
        profile__employee_code="E1",
        profile__affiliation_canton="VD",
    )
    bob = UserFactory(
        first_name="Bob",
        last_name="Brown",
        profile__employee_code="E2",
        profile__affiliation_canton="VS",
    )
    ValidatedTimesheetFactory(
        user=alice,
        date=DAY,
        time_helper=4.5,
        actor_count=1,
        leader_count=0,
        overtime=0,
        traveltime=1,
    )
    ValidatedTimesheetFactory(
        user=alice,
        date=DAY + datetime.timedelta(days=1),
        time_helper=4,
        actor_count=0,
        leader_count=1,
        overtime=0.5,
        traveltime=0,
    )
    ValidatedTimesheetFactory(
        user=bob, date=DAY, time_helper=9, leader_count=2, ignore=True
    )
    TimesheetFactory(
        user=UserFactory(first_name="Carl", profile__affiliation_canton="VD"),
        date=DAY,
        time_helper=4.5,
    )
    return alice, bob


class FrozenDate(datetime.date):
    @classmethod
    def today(cls):
        return cls(2019, 5, 2)


def test_winbiz_export_lines_per_category(timesheets):
    client = PowerUserAuthClient()
    with patch("apps.salary.views.timesheets.date", FrozenDate):
        response = client.get(export_url("accounting-export"))

    assert response.status_code == 200
    assert "export-winbiz-2019-4" in response["Content-Disposition"]
    rows = parse_csv(response, delimiter=";")
    assert all(row[:3] == ["02.05.2019", "4", "E1"] for row in rows)
    assert {row[3]: row[4] for row in rows} == {
        "1106": "1",
        "1105": "1",
        "1101": "8.5",
        "1102": "1.0",
        "1103": "0.5",
    }
    assert all(row[5:] == ["", "", "", "", "1", "Alice", "Anderson"] for row in rows)


def test_winbiz_export_filters_on_affiliation_canton(timesheets):
    client = PowerUserAuthClient()
    response = client.get(export_url("accounting-export") + "?canton=VS")

    assert response.status_code == 200
    assert parse_csv(response, delimiter=";") == []


def test_winbiz_export_without_validated_timesheets_is_404(db):
    client = PowerUserAuthClient()
    TimesheetFactory(date=DAY)
    assert client.get(export_url("accounting-export")).status_code == 404


@pytest.mark.xfail(
    raises=UnsupportedFormat,
    strict=True,
    reason="ExportMixin falls back to CSV for the filename only, not for the export",
)
def test_winbiz_export_unknown_format_falls_back_to_csv(timesheets):
    client = PowerUserAuthClient()
    response = client.get(export_url("accounting-export", fmt="foo"))
    assert response.status_code == 200
    assert response["Content-Disposition"].endswith('.csv"')


def test_control_export(timesheets):
    client = PowerUserAuthClient()
    response = client.get(export_url("control-export"))

    assert response.status_code == 200
    assert "export-control-2019-4" in response["Content-Disposition"]
    header, *rows = parse_csv(response)
    assert header[0] == "Numéro d’employé Crésus"
    assert header[3] == f"Heures moni·teur·trice ({HOURLY_RATE_HELPER}.-/h)"
    assert len(header) == 10
    by_code = {row[0]: row for row in rows}
    assert set(by_code) == {"E1", "E2"}
    alice_total_hours = 8.5 + 0.5 + 1
    assert by_code["E1"][1:] == [
        "Alice",
        "Anderson",
        "8.5",
        "1",
        "1",
        "0.5",
        "1.0",
        str(alice_total_hours),
        str(alice_total_hours * HOURLY_RATE_HELPER + RATE_ACTOR + BONUS_LEADER),
    ]
    assert by_code["E2"][3:] == ["0.0", "0", "0", "0.0", "0.0", "0.0", "0.0"]


def test_control_export_filters_on_affiliation_canton(timesheets):
    client = PowerUserAuthClient()
    response = client.get(export_url("control-export") + "?canton=VS")

    header, *rows = parse_csv(response)
    assert [row[0] for row in rows] == ["E2"]


def test_control_export_empty_month_has_only_headers(db):
    client = PowerUserAuthClient()
    response = client.get(export_url("control-export", year=2030, month=1))

    assert response.status_code == 200
    assert len(parse_csv(response)) == 1


def test_collaborator_export_only_contains_own_timesheets(timesheets):
    client = CollaboratorAuthClient()
    client.user.profile.employee_code = "MINE"
    client.user.profile.save()
    ValidatedTimesheetFactory(user=client.user, date=DAY, time_helper=2)

    response = client.get(export_url("control-export"))

    header, *rows = parse_csv(response)
    assert [row[0] for row in rows] == ["MINE"]


@pytest.mark.parametrize(
    "view_class, expected",
    [
        (ExportMonthlyTimesheets, "Export Winbiz 4 2019"),
        (ExportMonthlyControl, "Export de contrôle 4 2019"),
    ],
)
def test_export_dataset_title(view_class, expected):
    view = view_class(kwargs={"year": "2019", "month": "4"})
    view.request = RequestFactory().get("/")
    assert view.get_dataset_title() == expected
