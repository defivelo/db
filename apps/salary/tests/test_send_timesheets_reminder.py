import datetime

from django.core import mail
from django.urls import reverse

from apps.challenge.tests.factories import QualificationFactory, SessionFactory
from apps.common import DV_STATES
from apps.orga.tests.factories import OrganizationFactory
from apps.user.tests.factories import UserFactory
from defivelo.roles import user_cantons
from defivelo.tests.utils import AuthClient, StateManagerAuthClient

from .factories import TimesheetFactory, ValidatedTimesheetFactory


def test_reminder_preview_loads(db):
    client = StateManagerAuthClient()
    managed_cantons = user_cantons(client.user)

    QualificationFactory(
        actor=UserFactory(
            first_name="Maurice",
            last_name="Moss",
            profile__affiliation_canton=managed_cantons[0],
        ),
        session=SessionFactory(
            day=datetime.date(2019, 4, 11),
            orga=OrganizationFactory(address_canton=managed_cantons[0]),
        ),
    )

    response = client.get(
        reverse("salary:send-timesheets-reminder", kwargs={"year": 2019, "month": 4})
    )
    assert response.status_code == 200


def test_reminder_is_sent_to_helpers_with_missing_timesheets(db):
    client = StateManagerAuthClient()
    managed_cantons = user_cantons(client.user)

    # Helpers with all timesheets
    helper1 = UserFactory(profile__affiliation_canton=managed_cantons[0])
    helper2 = UserFactory(profile__affiliation_canton=managed_cantons[0])
    # Helper with missing timesheet
    helper3 = UserFactory(profile__affiliation_canton=managed_cantons[0])

    date1 = datetime.date(2019, 2, 11)
    date2 = datetime.date(2019, 2, 12)
    orga = OrganizationFactory(address_canton=managed_cantons[0])
    session1 = SessionFactory(day=date1, orga=orga)
    session2 = SessionFactory(day=date2, orga=orga)

    QualificationFactory(actor=helper1, session=session1)
    QualificationFactory(actor=helper1, session=session2)
    TimesheetFactory(user=helper1, date=date1)
    ValidatedTimesheetFactory(user=helper1, date=date2)

    QualificationFactory(actor=helper2, session=session1)
    TimesheetFactory(user=helper2, date=date1)

    QualificationFactory(actor=helper3, session=session1)
    QualificationFactory(actor=helper3, session=session2)
    TimesheetFactory(user=helper3, date=date1)

    mail.outbox = []
    response = client.post(
        reverse("salary:send-timesheets-reminder", kwargs={"year": 2019, "month": 2})
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert mail.outbox[0].recipients() == [helper3.email]


def test_reminder_is_not_sent_to_helper_of_other_canton(db):
    client = StateManagerAuthClient()

    assert DV_STATES[1] not in client.user.profile.managed_cantons  # invariant
    QualificationFactory(
        actor=UserFactory(profile__affiliation_canton=DV_STATES[1]),
        session=SessionFactory(
            day=datetime.date(2019, 2, 11),
            orga=OrganizationFactory(address_canton=DV_STATES[1]),
        ),
    )

    mail.outbox = []
    response = client.post(
        reverse("salary:send-timesheets-reminder", kwargs={"year": 2019, "month": 2})
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 0


def test_reminder_is_not_sent_to_helper_of_other_month(db):
    client = StateManagerAuthClient()
    managed_cantons = user_cantons(client.user)

    QualificationFactory(
        actor=UserFactory(profile__affiliation_canton=managed_cantons[0]),
        session=SessionFactory(day=datetime.date(2019, 1, 11)),
    )

    mail.outbox = []
    response = client.post(
        reverse("salary:send-timesheets-reminder", kwargs={"year": 2019, "month": 2})
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 0


def test_helper_cant_send_reminder(db):
    client = AuthClient()
    response = client.post(
        reverse("salary:send-timesheets-reminder", kwargs={"year": 2019, "month": 2})
    )
    assert response.status_code == 403
