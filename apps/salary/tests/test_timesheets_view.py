import datetime

from django.urls import reverse

from apps.challenge.tests.factories import QualificationFactory, SessionFactory
from defivelo.tests.utils import AuthClient


def test_helper_can_see_his_timesheet(db):
    client = AuthClient()

    QualificationFactory(
        actor=client.user, session=SessionFactory(day=datetime.date(2019, 4, 12)),
    )

    response = client.get(
        reverse(
            "salary:user-timesheets",
            kwargs={"year": 2019, "month": 4, "pk": client.user.pk},
        )
    )

    assert client.user.get_full_name() in response.content.decode()
    assert 1 == len(response.context["form"].forms)
