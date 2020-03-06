import datetime

import factory

from apps.salary.models import Timesheet
from apps.user.tests.factories import UserFactory


class TimesheetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Timesheet

    user = factory.SubFactory(UserFactory)
    date = factory.LazyFunction(lambda: datetime.date.today())


class ValidatedTimesheetFactory(TimesheetFactory):
    validated_at = factory.LazyAttribute(
        lambda timesheet: timesheet.date + datetime.timedelta(days=1)
    )
    validated_by = factory.SubFactory(UserFactory)
