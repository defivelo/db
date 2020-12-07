import datetime

from django.contrib.auth import get_user_model
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
        actor=client.user,
        session=SessionFactory(day=datetime.date(2019, 4, 12)),
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
        actor=user,
        session=SessionFactory(day=datetime.date(2019, 4, 11)),
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
        actor=user,
        session=SessionFactory(day=date),
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
        actor=user,
        session=SessionFactory(day=date),
    )
    ValidatedTimesheetFactory(
        date=date,
        user=user,
    )

    matrix = timesheets_overview.get_timesheets_status_matrix(2019, [user])

    assert user in matrix
    # Check that all months have "0" except for April that has a timesheet that is validated
    assert (
        matrix[user]
        == [0] * 3 + [timesheets_overview.TimesheetStatus.TIMESHEET_VALIDATED] + [0] * 8
    )


def test_orphaned_timesheets_in_a_month(db):
    user = UserFactory(
        first_name="Jen", last_name="Barber", profile__affiliation_canton="VD"
    )
    date = datetime.date(2019, 4, 11)
    ts = ValidatedTimesheetFactory(
        date=date,
        user=user,
    )

    orphaned_timesheets = timesheets_overview.get_orphaned_timesheets_per_month(
        date.year,
        users=get_user_model().objects.all(),
        month=date.month,
        cantons=["VD"],
    )

    # Check that our timesheet without a matching Qualification is in the orphaned set
    assert ts in orphaned_timesheets


def test_non_orphaned_timesheets_in_a_month(db):
    user = UserFactory(
        first_name="Jen", last_name="Barber", profile__affiliation_canton="VD"
    )
    date = datetime.date(2019, 4, 11)
    ts = ValidatedTimesheetFactory(
        date=date,
        user=user,
    )
    QualificationFactory(
        actor=user,
        session=SessionFactory(day=date),
    )

    orphaned_timesheets = timesheets_overview.get_orphaned_timesheets_per_month(
        date.year,
        users=get_user_model().objects.all(),
        month=date.month,
        cantons=["VD"],
    )

    # Check that our timesheet with a matching Qualification is not in the orphaned set
    assert ts not in orphaned_timesheets


def test_matrix_shows_timesheets_total(db):
    user = UserFactory(first_name="Jen", last_name="Barber")
    date = datetime.date(2019, 4, 11)
    QualificationFactory(
        actor=user,
        session=SessionFactory(day=date),
    )
    TimesheetFactory(date=date, user=user, overtime=5)

    amounts = timesheets_overview.get_timesheets_amount_by_month(2019, [user])

    # Check that all months have "0" except for April that has a timesheet that is validated
    assert amounts == [0] * 3 + [5 * HOURLY_RATE_HELPER] + [0] * 8


def test_state_manager_sees_reminder_button_for_month_with_missing_timesheets(db):
    client = StateManagerAuthClient()
    managed_cantons = user_cantons(client.user)

    helper = UserFactory(
        first_name="Maurice",
        last_name="Moss",
        profile__affiliation_canton=managed_cantons[0],
    )

    date_validated = datetime.date(2019, 2, 11)
    QualificationFactory(
        actor=helper,
        session=SessionFactory(day=date_validated),
    )
    TimesheetFactory(
        date=date_validated,
        user=helper,
    )

    date_missing = datetime.date(2019, 3, 11)
    QualificationFactory(
        actor=helper,
        session=SessionFactory(day=date_missing),
    )

    response = client.get(reverse("salary:timesheets-overview", kwargs={"year": 2019}))
    assert response.status_code == 200
    show_jan, show_feb, show_march, *_ = response.context["show_reminder_button_months"]
    assert not show_jan and not show_feb and show_march
    assert "Envoyer un rappel aux collabora" in response.content.decode()


def test_helper_doesnt_see_reminder_button(db):
    client = AuthClient()
    QualificationFactory(
        actor=client.user,
        session=SessionFactory(day=datetime.date(2019, 3, 11)),
    )
    response = client.get(reverse("salary:timesheets-overview", kwargs={"year": 2019}))
    assert response.status_code == 200
    assert "Envoyer un rappel aux collabora" not in response.content.decode()


def test_state_manager_sees_orphanage_fix_button_for_month_with_orphaned_timesheets(db):
    client = StateManagerAuthClient()
    managed_cantons = user_cantons(client.user)

    helper = UserFactory(
        first_name="Maurice",
        last_name="Moss",
        profile__affiliation_canton=managed_cantons[0],
    )
    helper.profile.save()

    date_ts = datetime.date(2019, 4, 11)
    ts = TimesheetFactory(
        date=date_ts,
        user=helper,
    )
    # Create a Qualification, but at a different date
    date_quali = datetime.date(2019, 4, 15)
    QualificationFactory(
        actor=helper,
        session=SessionFactory(day=date_quali, orga__address_canton=managed_cantons[0]),
    )

    response = client.get(reverse("salary:timesheets-overview", kwargs={"year": 2019}))

    assert response.status_code == 200
    assert response.context["orphaned_timesheets"][1] == set()
    assert response.context["orphaned_timesheets"][2] == set()
    assert response.context["orphaned_timesheets"][3] == set()
    assert ts in response.context["orphaned_timesheets"][4]

    assert "1 entrée orpheline" in response.content.decode()
