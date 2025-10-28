import datetime

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.challenge.tests.factories import QualificationFactory, SessionFactory
from apps.common import DV_STATES
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import AuthClient, PowerUserAuthClient, StateManagerAuthClient

from .. import timesheets_overview
from ..models import MonthlyCantonalValidation, MonthlyCantonalValidationUrl
from .factories import MonthlyCantonalValidationFactory, TimesheetFactory


class MCVTestCase(TestCase):
    def test_no_two_identical_month_canton(self):
        today = datetime.datetime.today().replace(day=4)
        mcv = MonthlyCantonalValidationFactory(canton="VD", date=today)
        # Day is reset to start of the month; day=1
        self.assertEqual(mcv.date.day, 1, mcv)

        with self.assertRaises(IntegrityError):
            MonthlyCantonalValidationFactory(canton="VD", date=today.replace(day=8))


class AuthUserTest(TestCase):
    def setUp(self):
        self.client = AuthClient()
        super().setUp()

    def test_no_access_to_mcvs_lists(self):
        today = datetime.datetime.today()
        url = reverse(
            "salary:validations-month",
            kwargs={"month": today.month, "year": today.year},
        )
        # Final URL is forbidden
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403, url)
        url = reverse(
            "salary:validations-year",
            kwargs={"year": today.year},
        )
        # Final URL is forbidden
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403, url)

    def test_no_access_to_mcvs_updates(self):
        today = datetime.datetime.today()
        for canton in DV_STATES:
            url = reverse(
                "salary:validation-update",
                kwargs={"month": today.month, "year": today.year, "canton": canton},
            )
            # Final URL is forbidden
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 403, url)


class StateManagerUserTest(TestCase):
    def setUp(self):
        self.client = StateManagerAuthClient()
        # Our migrations create two for us
        self.urls = MonthlyCantonalValidationUrl.objects.all()
        super().setUp()

    def test_access_to_mcvs_lists(self):
        today = datetime.datetime.today()
        url = reverse(
            "salary:validations-month",
            kwargs={"month": today.month, "year": today.year},
        )
        # Final URL is accessible
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, url)

        url = reverse(
            "salary:validations-year",
            kwargs={"year": today.year},
        )
        # Final URL is accessible
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, url)

    def test_access_to_my_mcvs_updates(self):
        today = datetime.datetime.today()
        managed_cantons = [c.canton for c in self.client.user.managedstates.all()]
        for canton in DV_STATES:
            mcv_kwargs = {"month": today.month, "year": today.year, "canton": canton}
            url = reverse("salary:validation-update", kwargs=mcv_kwargs)
            mcv_gs = MonthlyCantonalValidation.objects.filter(
                canton=canton, date=today.replace(day=1)
            )
            # They don't exist before we access them
            self.assertFalse(mcv_gs.exists())
            # Final URL is accessible if in my cantons
            response = self.client.get(url, follow=True)
            if canton in managed_cantons:
                self.assertEqual(response.status_code, 200, url)
                # We looked at it, it exists now
                self.assertTrue(mcv_gs.exists())
                # Try to validate without ticking anything
                response = self.client.post(url, {})
                self.assertEqual(response.status_code, 302, url)

                # Get the object, and assert that it didn't get validated for real
                mcv = mcv_gs.first()
                self.assertFalse(mcv.validated, mcv)

                # Try to validate with the urls ticked only
                initial = {}
                for u in self.urls:
                    initial[f"url_{u.pk}"] = True
                response = self.client.post(url, initial)
                self.assertEqual(response.status_code, 302, url)

                # Get the object, and assert that it didn't get validated for real
                mcv = mcv_gs.first()
                self.assertFalse(mcv.validated, mcv)
                # But the URLs are now present
                self.assertEqual(
                    set(mcv.validated_urls.all().values_list("pk", flat=True)),
                    set(self.urls.values_list("pk", flat=True)),
                )

                # Now also make sure the timesheets of the month are all valid
                actor = UserFactory(
                    profile__affiliation_canton=canton,
                )
                QualificationFactory(
                    actor=actor,
                    session=SessionFactory(
                        day=today.replace(day=12),
                    ),
                )
                # For now there is no timesheet
                initial["validated"] = True
                response = self.client.post(url, initial)
                self.assertEqual(response.status_code, 200, url)
                # The error code is a 200, as the post failed

                TimesheetFactory(
                    user=actor,
                    date=today.replace(day=12),
                    validated_at=today.replace(day=13),
                    validated_by=actor,
                )
                # Clear the cache
                timesheets_overview.timesheets_validation_status.all_users = {}
                # So post with all ticks ticked
                initial["timesheets_checked"] = True
                response = self.client.post(url, initial)
                self.assertEqual(response.status_code, 302, url)
                # The error code is a 302, as the post succeeded
                mcv = mcv_gs.first()
                self.assertTrue(mcv.validated, mcv)
                self.assertEqual(mcv.validated_by, self.client.user, mcv)
                self.assertTrue(mcv.validated_at is not None, mcv)
                # Now that it's validated, assert it can't be unvalidated
                initial["validated"] = False
                response = self.client.post(url, initial)
                self.assertEqual(response.status_code, 302, url)
                # It's still validated
                self.assertTrue(mcv_gs.first().validated)
            else:
                self.assertEqual(response.status_code, 403, url)
                # We looked at it, but it does not exist now
                self.assertFalse(mcv_gs.exists())
                # Assert that it can't be posted to either
                response = self.client.post(url, {"validated": True})
                self.assertEqual(response.status_code, 403, url)


class PowerUserTest(TestCase):
    def setUp(self):
        self.client = PowerUserAuthClient()
        super().setUp()

    def test_access_to_mcvs_lists(self):
        today = datetime.datetime.today()
        url = reverse(
            "salary:validations-month",
            kwargs={"month": today.month, "year": today.year},
        )
        # Final URL is accessible
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, url)

        url = reverse(
            "salary:validations-year",
            kwargs={"year": today.year},
        )
        # Final URL is accessible
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, url)

    def test_access_to_all_mcvs_updates(self):
        today = datetime.datetime.today()
        for canton in DV_STATES:
            url = reverse(
                "salary:validation-update",
                kwargs={"month": today.month, "year": today.year, "canton": canton},
            )
            # Final URL is accessible
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)
