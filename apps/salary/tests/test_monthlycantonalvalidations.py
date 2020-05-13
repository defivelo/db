import datetime

from django.db import IntegrityError
from django.test import TestCase

from .factories import MonthlyCantonalValidationFactory


class MCVTestCase(TestCase):
    def test_no_two_identical_month_canton(self):
        today = datetime.datetime.today()
        MonthlyCantonalValidationFactory(canton="VD", date=today)

        with self.assertRaises(IntegrityError):
            MonthlyCantonalValidationFactory(canton="VD", date=today)
