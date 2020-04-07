import datetime

from django.urls import reverse

from apps.challenge.tests.factories import QualificationFactory, SessionFactory
from apps.salary import HOURLY_RATE_HELPER, timesheets_overview
from apps.user.tests.factories import UserFactory
from defivelo.roles import user_cantons
from defivelo.tests.utils import AuthClient, PowerUserAuthClient, StateManagerAuthClient

from .factories import TimesheetFactory, ValidatedTimesheetFactory


def test_power_user_can_see_all_users_in_overview(db):
    client = PowerUserAuthClient()
    QualificationFactory(
        actor=UserFactory(first_name="Maurice", last_name="Moss"),
        session=SessionFactory(day=datetime.date(2019, 4, 11)),
    )

    response = client.get(reverse("salary:timesheets-overview", kwargs={"year": 2019}))

    assert "Maurice Moss" in response.content.decode()


def test_state_manager_can_only_see_managed_users(db):
    client = StateManagerAuthClient()
    managed_cantons = user_cantons(client.user)

    QualificationFactory(
        actor=UserFactory(
            first_name="Maurice",
            last_name="Moss",
            profile__affiliation_canton=managed_cantons[0],
        ),
        session=SessionFactory(day=datetime.date(2019, 4, 11)),
    )
    QualificationFactory(
        actor=UserFactory(
            first_name="Jen", last_name="Barber", profile__affiliation_canton="GE"
        ),
        session=SessionFactory(day=datetime.date(2019, 4, 20)),
    )

    response = client.get(reverse("salary:timesheets-overview", kwargs={"year": 2019}))

    assert "Maurice Moss" in response.content.decode()
    assert "Jen Barber" not in response.content.decode()


def test_helper_can_only_see_own_entries(db):
    client = AuthClient()
    client.user.profile.affiliation_canton = "VD"

    QualificationFactory(
        actor=UserFactory(
            first_name="Jen", last_name="Barber", profile__affiliation_canton="VD"
        ),
        session=SessionFactory(day=datetime.date(2019, 4, 11)),
    )
    QualificationFactory(
        actor=client.user, session=SessionFactory(day=datetime.date(2019, 4, 12)),
    )

    response = client.get(reverse("salary:timesheets-overview", kwargs={"year": 2019}))

    assert (
        reverse(
            "salary:user-timesheets",
            kwargs={"year": 2019, "month": 4, "pk": client.user.pk},
        )
        in response.content.decode()
    )
    assert "Jen Barber" not in response.content.decode()


def test_matrix_shows_months_with_missing_timesheets(db):
    user = UserFactory(first_name="Jen", last_name="Barber")
    QualificationFactory(
        actor=user, session=SessionFactory(day=datetime.date(2019, 4, 11)),
    )

    matrix = timesheets_overview.get_timesheets_status_matrix(2019, [user])

    assert user in matrix
    # Check that all months have "0" (ie. no status), except for April that has a
    # missing timesheet
    assert (
        matrix[user]
        == [0] * 3 + [timesheets_overview.TimesheetStatus.TIMESHEET_MISSING] + [0] * 8
    )


def test_matrix_shows_months_with_non_validated_timesheets(db):
    user = UserFactory(first_name="Jen", last_name="Barber")
    date = datetime.date(2019, 4, 11)
    QualificationFactory(
        actor=user, session=SessionFactory(day=date),
    )
    TimesheetFactory(date=date, user=user)

    matrix = timesheets_overview.get_timesheets_status_matrix(2019, [user])

    assert user in matrix
    # Check that all months have "0" except for April that has a timesheet awaiting
    # validation
    assert (
        matrix[user]
        == [0] * 3
        + [timesheets_overview.TimesheetStatus.TIMESHEET_NOT_VALIDATED]
        + [0] * 8
    )


def test_matrix_shows_months_with_validated_timesheets(db):
    user = UserFactory(first_name="Jen", last_name="Barber")
    date = datetime.date(2019, 4, 11)
    QualificationFactory(
        actor=user, session=SessionFactory(day=date),
    )
    ValidatedTimesheetFactory(
        date=date, user=user,
    )

    matrix = timesheets_overview.get_timesheets_status_matrix(2019, [user])

    assert user in matrix
    # Check that all months have "0" except for April that has a timesheet that is validated
    assert (
        matrix[user]
        == [0] * 3 + [timesheets_overview.TimesheetStatus.TIMESHEET_VALIDATED] + [0] * 8
    )


def test_matrix_shows_timesheets_total(db):
    user = UserFactory(first_name="Jen", last_name="Barber")
    date = datetime.date(2019, 4, 11)
    QualificationFactory(
        actor=user, session=SessionFactory(day=date),
    )
    TimesheetFactory(date=date, user=user, overtime=5)

    amounts = timesheets_overview.get_timesheets_amount_by_month(2019, [user])

    # Check that all months have "0" except for April that has a timesheet that is validated
    assert amounts == [0] * 3 + [5 * HOURLY_RATE_HELPER] + [0] * 8
