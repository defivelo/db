import datetime

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.common import DV_STATES
from defivelo.tests.utils import AuthClient, PowerUserAuthClient, StateManagerAuthClient

from ..models import MonthlyCantonalValidation
from .factories import MonthlyCantonalValidationFactory


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
                for validated in [False, True]:
                    # Now try to update without validating first; then validate
                    initial = {}
                    if validated:
                        initial["validated"] = True
                    response = self.client.post(url, initial)
                    self.assertEqual(response.status_code, 302, url)

                    # Get the object, and assert that it got validated (or not) for real
                    mcv = mcv_gs.first()
                    self.assertEqual(mcv.validated, validated)
                    if validated:
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
