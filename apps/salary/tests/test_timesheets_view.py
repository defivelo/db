import datetime

from django.urls import reverse

from apps.challenge.tests.factories import (
    QualificationFactory,
    SeasonFactory,
    SessionFactory,
)
from apps.common import DV_SEASON_SPRING
from apps.orga.tests.factories import OrganizationFactory
from apps.salary.models import Timesheet
from apps.user.tests.factories import UserFactory
from defivelo.roles import user_cantons
from defivelo.tests.utils import AuthClient, StateManagerAuthClient


def test_helper_can_see_his_timesheet(db):
    client = AuthClient()

    SeasonFactory(
        cantons=["VD"], year=2019, season=DV_SEASON_SPRING,
    )
    QualificationFactory(
        actor=client.user,
        session=SessionFactory(
            day=datetime.date(2019, 4, 12),
            orga=OrganizationFactory(address_canton="VD"),
        ),
    )

    response = client.get(
        reverse(
            "salary:user-timesheets",
            kwargs={"year": 2019, "month": 4, "pk": client.user.pk},
        )
    )

    assert client.user.get_full_name() in response.content.decode()
    assert 1 == len(response.context["form"].forms)


def test_helper_cannot_timesheet_overtime_without_comments(db):
    client = AuthClient()

    SeasonFactory(
        cantons=["VD"], year=2019, season=DV_SEASON_SPRING,
    )
    QualificationFactory(
        actor=client.user,
        session=SessionFactory(
            day=datetime.date(2019, 4, 12),
            orga=OrganizationFactory(address_canton="VD"),
        ),
    )

    datas = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "0",
        "form-0-date": "2019-04-12",
        "form-0-time_helper": "4.5",
        "form-0-actor_count": "0",
        "form-0-leader_count": "0",
        "form-0-overtime": "0.25",
        "form-0-traveltime": "0.25",
        "form-0-comments": "",
    }

    client.post(
        reverse(
            "salary:user-timesheets",
            kwargs={"year": 2019, "month": 4, "pk": client.user.pk},
        ),
        datas,
    )
    assert Timesheet.objects.count() == 0


def test_helper_can_timesheet(db):
    client = AuthClient()

    SeasonFactory(
        cantons=["VD"], year=2019, season=DV_SEASON_SPRING,
    )
    QualificationFactory(
        actor=client.user,
        session=SessionFactory(
            day=datetime.date(2019, 4, 12),
            orga=OrganizationFactory(address_canton="VD"),
        ),
    )

    datas = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "0",
        "form-0-date": "2019-04-12",
        "form-0-time_helper": "4.5",
        "form-0-actor_count": "0",
        "form-0-leader_count": "0",
        "form-0-overtime": "0.25",
        "form-0-traveltime": "0.25",
        "form-0-comments": "I took longer",
    }

    client.post(
        reverse(
            "salary:user-timesheets",
            kwargs={"year": 2019, "month": 4, "pk": client.user.pk},
        ),
        datas,
    )
    assert Timesheet.objects.count() == 1


def test_helper_can_update_timesheet(db):
    client = AuthClient()

    SeasonFactory(
        cantons=["VD"], year=2019, season=DV_SEASON_SPRING,
    )
    QualificationFactory(
        actor=client.user,
        session=SessionFactory(
            day=datetime.date(2019, 4, 12),
            orga=OrganizationFactory(address_canton="VD"),
        ),
    )

    datas = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "0",
        "form-0-date": "2019-04-12",
        "form-0-time_helper": "4.5",
        "form-0-actor_count": "0",
        "form-0-leader_count": "0",
        "form-0-overtime": "0.25",
        "form-0-traveltime": "0.25",
        "form-0-comments": "Initial comment",
    }

    client.post(
        reverse(
            "salary:user-timesheets",
            kwargs={"year": 2019, "month": 4, "pk": client.user.pk},
        ),
        datas,
    )
    datas["form-0-overtime"] = 1
    datas["form-0-comments"] = "New comment"
    client.post(
        reverse(
            "salary:user-timesheets",
            kwargs={"year": 2019, "month": 4, "pk": client.user.pk},
        ),
        datas,
    )
    assert (
        Timesheet.objects.count() == 1
        and Timesheet.objects.first().overtime == 1
        and Timesheet.objects.first().comments == "New comment"
    )


def test_helper_cannot_validate_timesheet(db):
    client = AuthClient()

    SeasonFactory(
        cantons=["VD"], year=2019, season=DV_SEASON_SPRING,
    )
    QualificationFactory(
        actor=client.user,
        session=SessionFactory(
            day=datetime.date(2019, 4, 12),
            orga=OrganizationFactory(address_canton="VD"),
        ),
    )

    datas = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "0",
        "form-0-date": "2019-04-12",
        "form-0-time_helper": "4.5",
        "form-0-actor_count": "0",
        "form-0-leader_count": "0",
        "form-0-overtime": "0.25",
        "form-0-traveltime": "0.25",
        "form-0-comments": "Comment",
        "form-0-validated": True,
    }

    client.post(
        reverse(
            "salary:user-timesheets",
            kwargs={"year": 2019, "month": 4, "pk": client.user.pk},
        ),
        datas,
    )
    assert (
        Timesheet.objects.count() == 1
        and Timesheet.objects.first().validated_at == None
    )


def test_state_manager_can_validate_timesheet(db):
    client = StateManagerAuthClient()
    managed_cantons = user_cantons(client.user)
    actor = UserFactory(
        first_name="Maurice",
        last_name="Moss",
        profile__affiliation_canton=managed_cantons[0],
    )
    SeasonFactory(
        cantons=[managed_cantons[0]], year=2019, season=DV_SEASON_SPRING,
    )
    QualificationFactory(
        actor=actor,
        session=SessionFactory(
            day=datetime.date(2019, 4, 12),
            orga=OrganizationFactory(address_canton=managed_cantons[0]),
        ),
    )

    datas = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "0",
        "form-0-date": "2019-04-12",
        "form-0-time_helper": "4.5",
        "form-0-actor_count": "0",
        "form-0-leader_count": "0",
        "form-0-overtime": "0.25",
        "form-0-traveltime": "0.25",
        "form-0-comments": "Comment",
        "form-0-validated": True,
    }

    client.post(
        reverse(
            "salary:user-timesheets", kwargs={"year": 2019, "month": 4, "pk": actor.pk},
        ),
        datas,
    )
    assert Timesheet.objects.count() == 1 and Timesheet.objects.first().validated_at


def test_helper_cannot_timesheet_if_he_has_not_work(db):
    client = AuthClient()
    datas = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "0",
        "form-0-date": "2019-04-12",
        "form-0-time_helper": "4.5",
        "form-0-actor_count": "0",
        "form-0-leader_count": "0",
        "form-0-overtime": "0.25",
        "form-0-traveltime": "0.25",
        "form-0-comments": "Comment",
    }

    client.post(
        reverse(
            "salary:user-timesheets",
            kwargs={"year": 2019, "month": 4, "pk": client.user.pk},
        ),
        datas,
    )
    assert Timesheet.objects.count() == 0
