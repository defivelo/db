import datetime

from django.db import IntegrityError
from django.test import TestCase

from .factories import MonthlyCantonalValidationFactory

from defivelo.tests.utils import AuthClient
from django.urls import reverse


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
        super(AuthUserTest, self).setUp()

    def test_no_access_to_mcvs_lists(self):
        today = datetime.datetime.today()
        url = reverse(
            "salary:validations-month",
            kwargs={"month": today.month, "year": today.year},
        )
        # Final URL is forbidden
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403, url)
