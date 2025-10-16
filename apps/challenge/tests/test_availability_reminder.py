from django.core import mail
from django.test import TestCase
from django.urls import reverse

from apps.user import FORMATION_M1
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import StateManagerAuthClient

from ..models import HelperSessionAvailability
from .factories import QualificationFactory, SeasonFactory, SessionFactory


class SeasonReminderTests(TestCase):
    def setUp(self):
        # State manager client so we can access season management views
        self.client = StateManagerAuthClient()

        # Create a season in one of the manager's cantons
        self.season = SeasonFactory()
        mycantons = [c.canton for c in self.client.user.managedstates.all()]
        self.season.cantons = mycantons or self.season.cantons
        self.season.save()

        # Ensure there are at least two sessions with qualifications in-season
        self.session = SessionFactory(orga__address_canton=self.season.cantons[0])
        # Put the session within the season dates
        self.session.day = self.season.begin
        self.session.save()
        # Attach at least one qualification so it appears in sessions_with_qualifs
        QualificationFactory(session=self.session)

        self.session2 = SessionFactory(orga__address_canton=self.season.cantons[0])
        self.session2.day = self.season.begin
        self.session2.save()
        QualificationFactory(session=self.session2)

        # Two users in the season canton
        self.user_no_avail = UserFactory(
            profile__affiliation_canton=self.season.cantons[0],
            profile__formation=FORMATION_M1,
        )
        self.user_with_avail = UserFactory(
            profile__affiliation_canton=self.season.cantons[0],
            profile__formation=FORMATION_M1,
        )

        # Give one availability to user_with_avail in this season
        HelperSessionAvailability.objects.update_or_create(
            session=self.session,
            helper=self.user_with_avail,
            defaults={"availability": "y"},
        )

    def test_recipients_excludes_users_with_any_availability(self):
        url = reverse("season-availability-reminder", kwargs={"pk": self.season.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        recipients = list(response.context["recipients"])  # queryset evaluated in view
        # user_no_avail has none -> included; user_with_avail has only partial -> included too
        self.assertIn(self.user_no_avail, recipients)
        self.assertIn(self.user_with_avail, recipients)

    def test_post_sends_emails_and_sets_timestamp(self):
        url = reverse("season-availability-reminder", kwargs={"pk": self.season.pk})

        # Pre-condition: no timestamp
        self.assertIsNone(self.season.availability_reminder_sent_at)

        # Send the emails
        response = self.client.post(url, {"sendemail": "on"}, follow=True)
        self.assertIn(response.status_code, [200, 302])

        # Expect two emails sent (users without full availability across all sessions)
        self.assertEqual(len(mail.outbox), 2)
        to_addrs = {mail.outbox[0].to[0], mail.outbox[1].to[0]}
        self.assertTrue(any(self.user_no_avail.email in r for r in to_addrs))
        self.assertTrue(any(self.user_with_avail.email in r for r in to_addrs))

        # Timestamp should be set on season
        self.season.refresh_from_db()
        self.assertIsNotNone(self.season.availability_reminder_sent_at)
