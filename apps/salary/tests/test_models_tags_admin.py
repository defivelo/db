import datetime

from django.contrib.admin.sites import AdminSite

import pytest

from apps.salary import BONUS_LEADER, HOURLY_RATE_HELPER, RATE_ACTOR
from apps.salary.admin import MonthlyCantonalValidationUrlAdmin
from apps.salary.models import MonthlyCantonalValidation, MonthlyCantonalValidationUrl
from apps.salary.templatetags.salary_tags import timesheet_status_css_class
from apps.salary.timesheets_overview import TimesheetStatus
from apps.user.tests.factories import UserFactory

from .factories import MonthlyCantonalValidationFactory, TimesheetFactory


@pytest.fixture
def timesheet(db):
    return TimesheetFactory(
        time_helper=4, overtime=1, traveltime=1, actor_count=2, leader_count=3
    )


def test_timesheet_amounts(timesheet):
    assert timesheet.get_total_amount_helper() == 6 * HOURLY_RATE_HELPER
    assert timesheet.get_total_amount_actor() == 2 * RATE_ACTOR
    assert timesheet.get_total_amount_leader() == 3 * BONUS_LEADER
    assert timesheet.get_total_amount() == (
        6 * HOURLY_RATE_HELPER + 2 * RATE_ACTOR + 3 * BONUS_LEADER
    )


def test_ignored_timesheet_amounts_are_zero(timesheet):
    timesheet.ignore = True
    assert timesheet.get_total_amount_helper() == 0
    assert timesheet.get_total_amount_actor() == 0
    assert timesheet.get_total_amount_leader() == 0
    assert timesheet.get_total_amount() == 0


def test_validation_url_str(db):
    url = MonthlyCantonalValidationUrl.objects.create(
        name="Check", url="https://example.com"
    )
    assert str(url) == "Check"


def test_monthly_cantonal_validation_str(db):
    mcv = MonthlyCantonalValidationFactory(canton="VD", date=datetime.date(2019, 4, 15))
    assert str(mcv) == "2019/4: Validation du canton VD"


def test_validated_requires_validated_by(db):
    mcv = MonthlyCantonalValidationFactory(
        canton="VD",
        validated_at=datetime.datetime(2019, 4, 1, tzinfo=datetime.timezone.utc),
    )
    assert mcv.validated is False


def test_validated_requires_validated_at(db):
    mcv = MonthlyCantonalValidationFactory(canton="VD", validated_by=UserFactory())
    assert mcv.validated is False


def test_validated_requires_all_urls(db):
    extra_url = MonthlyCantonalValidationUrl.objects.create(
        name="A", url="https://a.example.com"
    )
    mcv = MonthlyCantonalValidationFactory(
        canton="VD",
        validated_at=datetime.datetime(2019, 4, 1, tzinfo=datetime.timezone.utc),
        validated_by=UserFactory(),
    )
    mcv.validated_urls.set(
        MonthlyCantonalValidationUrl.objects.exclude(pk=extra_url.pk)
    )
    assert mcv.validated is False

    mcv.validated_urls.add(extra_url)
    assert MonthlyCantonalValidation.objects.get(pk=mcv.pk).validated is True


@pytest.mark.parametrize(
    "status, expected",
    [
        (TimesheetStatus.TIMESHEET_MISSING, "danger"),
        (
            TimesheetStatus.TIMESHEET_MISSING | TimesheetStatus.TIMESHEET_VALIDATED,
            "danger",
        ),
        (TimesheetStatus.TIMESHEET_NOT_VALIDATED, "warning"),
        (
            TimesheetStatus.TIMESHEET_NOT_VALIDATED
            | TimesheetStatus.TIMESHEET_VALIDATED,
            "warning",
        ),
        (TimesheetStatus.TIMESHEET_VALIDATED, "success"),
        (0, ""),
    ],
)
def test_timesheet_status_css_class(status, expected):
    assert timesheet_status_css_class(status) == expected


def test_admin_missing_languages_lists_untranslated(db):
    url = MonthlyCantonalValidationUrl.objects.create(
        name="A", url="https://a.example.com"
    )
    admin = MonthlyCantonalValidationUrlAdmin(MonthlyCantonalValidationUrl, AdminSite())
    assert admin.missing_languages(url) == "de"


def test_admin_missing_languages_all_translated(db):
    url = MonthlyCantonalValidationUrl.objects.create(
        name="A", url="https://a.example.com"
    )
    url.set_current_language("de")
    url.name = "A de"
    url.url = "https://a.example.de"
    url.save()
    admin = MonthlyCantonalValidationUrlAdmin(MonthlyCantonalValidationUrl, AdminSite())
    assert "icon-yes.svg" in admin.missing_languages(url)
