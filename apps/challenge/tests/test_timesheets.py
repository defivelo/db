import datetime

from django.urls import reverse

from apps.salary.models import Timesheet
from apps.salary.tests.factories import TimesheetFactory
from apps.user.tests.factories import UserFactory

from .. import CHOSEN_AS_ACTOR
from ..models import HelperSessionAvailability
from .factories import (
    QualificationActivityFactory,
    QualificationFactory,
    SessionFactory,
)
from .test_seasons import PowerUserTest as SeasonPowerUserTest


class TimesheetsTestCase(SeasonPowerUserTest):
    def test_related_timesheets_are_displayed_on_quali_edition(self):
        user = self.client.user
        session1 = self.sessions[0]
        quali = QualificationFactory(actor=user, session=session1)
        session2 = SessionFactory(
            orga=session1.orga, day=session1.day + datetime.timedelta(weeks=5)
        )
        QualificationFactory(actor=user, session=session2)

        timesheet1 = TimesheetFactory(user=user, date=self.sessions[0].day)
        timesheet2 = TimesheetFactory(user=user, date=session2.day)

        response = self.client.get(
            reverse(
                "quali-update",
                kwargs={
                    "pk": quali.pk,
                    "seasonpk": self.season.pk,
                    "sessionpk": session1.pk,
                },
            )
        )
        content = response.rendered_content

        # Related timesheet
        assert (
            reverse(
                "salary:user-timesheets",
                kwargs={
                    "year": timesheet1.date.year,
                    "month": timesheet1.date.month,
                    "pk": user.pk,
                },
            )
            in content
        )

        # Non related timesheet
        assert (
            reverse(
                "salary:user-timesheets",
                kwargs={
                    "year": timesheet2.date.year,
                    "month": timesheet2.date.month,
                    "pk": user.pk,
                },
            )
            not in content
        )

    def test_timesheets_are_displayed_on_quali_deletion(self):
        user = self.client.user
        session1 = self.sessions[0]
        quali = QualificationFactory(actor=user, session=session1)
        session2 = SessionFactory(
            orga=session1.orga, day=session1.day + datetime.timedelta(weeks=5)
        )
        QualificationFactory(actor=user, session=session2)

        timesheet1 = TimesheetFactory(user=user, date=session1.day)
        timesheet2 = TimesheetFactory(user=user, date=session2.day)

        response = self.client.get(
            reverse(
                "quali-delete",
                kwargs={
                    "pk": quali.pk,
                    "seasonpk": self.season.pk,
                    "sessionpk": session1.pk,
                },
            )
        )

        content = response.rendered_content

        # Related timesheet
        assert (
            reverse(
                "salary:user-timesheets",
                kwargs={
                    "year": timesheet1.date.year,
                    "month": timesheet1.date.month,
                    "pk": user.pk,
                },
            )
            in content
        )

        # Non related timesheet
        assert (
            reverse(
                "salary:user-timesheets",
                kwargs={
                    "year": timesheet2.date.year,
                    "month": timesheet2.date.month,
                    "pk": user.pk,
                },
            )
            not in content
        )

    def test_day_is_enabled_on_session_edition_if_no_timesheet_exist(self):
        response = self.client.get(
            reverse(
                "session-update",
                kwargs={"pk": self.sessions[0].pk, "seasonpk": self.season.pk},
            )
        )
        assert (
            not response.context["form"]
            .fields["day"]
            .widget.attrs.get("readonly", False)
        )

    def test_day_is_disabled_on_session_edition_if_a_timesheet_exists(self):
        user = self.client.user
        QualificationFactory(actor=user, session=self.sessions[0])
        TimesheetFactory(user=user, date=self.sessions[0].day)

        response = self.client.get(
            reverse(
                "session-update",
                kwargs={"pk": self.sessions[0].pk, "seasonpk": self.season.pk},
            )
        )
        assert (
            response.context["form"].fields["day"].widget.attrs.get("readonly", False)
        )

    def test_specific_timesheets_are_deleted_on_quali_edition(self):
        user1 = self.client.user
        user1_activity = QualificationActivityFactory()
        user1.profile.actor_for.add(user1_activity)
        user2 = UserFactory()
        session = self.sessions[0]

        HelperSessionAvailability.objects.create(
            session=session, helper=user1, availability="y", chosen_as=CHOSEN_AS_ACTOR
        )

        quali = QualificationFactory(actor=user1, leader=user2, session=session)

        timesheet1_pk = TimesheetFactory(user=user1, date=session.day).pk
        timesheet2_pk = TimesheetFactory(user=user2, date=session.day).pk

        self.client.post(
            reverse(
                "quali-update",
                kwargs={
                    "pk": quali.pk,
                    "seasonpk": self.season.pk,
                    "sessionpk": session.pk,
                },
            ),
            data={
                "session": session.pk,
                "name": quali.name,
                "class_teacher_fullname": "Nina Strahm",
                "class_teacher_natel": "+41319242400",
                "n_participants": "25",
                "n_bikes": "",
                "n_helmets": "0",
                "leader": "",
                "helpers[]": "",
                "activity_A": "2",
                "activity_B": "4",
                "activity_C": user1_activity.pk,
                "actor": user1.pk,
                "comments": "The leader has been removed",
            },
        )

        assert Timesheet.objects.filter(pk=timesheet1_pk).exists()
        assert not Timesheet.objects.filter(pk=timesheet2_pk).exists()

    def test_timesheets_are_deleted_on_quali_deletion(self):
        user = self.client.user
        session = self.sessions[0]
        quali = QualificationFactory(actor=user, session=session)
        timesheet1_pk = TimesheetFactory(user=user, date=session.day).pk
        timesheet2_pk = TimesheetFactory(
            user=user, date=session.day + datetime.timedelta(days=1)
        ).pk

        self.client.post(
            reverse(
                "quali-delete",
                kwargs={
                    "pk": quali.pk,
                    "seasonpk": self.season.pk,
                    "sessionpk": session.pk,
                },
            )
        )

        assert not Timesheet.objects.filter(pk=timesheet1_pk).exists()
        assert Timesheet.objects.filter(pk=timesheet2_pk).exists()

    def test_timesheets_are_deleted_on_session_deletion(self):
        user = self.client.user
        session = self.sessions[0]
        QualificationFactory(actor=user, session=session)
        timesheet1_pk = TimesheetFactory(user=user, date=session.day).pk
        timesheet2_pk = TimesheetFactory(
            user=user, date=session.day + datetime.timedelta(days=1)
        ).pk

        self.client.post(
            reverse(
                "session-delete",
                kwargs={
                    "pk": session.pk,
                    "seasonpk": self.season.pk,
                },
            )
        )

        assert not Timesheet.objects.filter(pk=timesheet1_pk).exists()
        assert Timesheet.objects.filter(pk=timesheet2_pk).exists()
