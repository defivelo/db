import datetime

from django.db import IntegrityError
from django.test import TestCase

from .factories import MonthlyCantonalValidationFactory


class MCVTestCase(TestCase):
    def test_no_two_identical_month_canton(self):
        today = datetime.datetime.today().replace(day=4)
        mcv = MonthlyCantonalValidationFactory(canton="VD", date=today)
        # Day is reset to start of the month; day=1
        self.assertEqual(mcv.date.day, 1, mcv)

        with self.assertRaises(IntegrityError):
            MonthlyCantonalValidationFactory(canton="VD", date=today.replace(day=8))
