import datetime

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse

import pytest

from apps.challenge.tests.factories import QualificationFactory, SessionFactory
from apps.orga.tests.factories import OrganizationFactory
from apps.salary import timesheets_overview
from apps.salary.models import Timesheet
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import (
    AuthClient,
    CollaboratorAuthClient,
    PowerUserAuthClient,
    StateManagerAuthClient,
)

from .factories import TimesheetFactory

DAY = datetime.date(2019, 4, 12)


def cleanup_url(year=2019, month=4):
    return reverse("salary:cleanup-timesheets", kwargs={"year": year, "month": month})


def overview_url(year=2019):
    return reverse("salary:timesheets-overview", kwargs={"year": year})


def test_my_timesheets_redirects_to_own_timesheets(db):
    client = CollaboratorAuthClient()
    response = client.get(
        reverse("salary:my-timesheets", kwargs={"year": 2019, "month": 4})
    )
    assert response.status_code == 302
    assert response.url == reverse(
        "salary:user-timesheets",
        kwargs={"year": "2019", "month": "4", "pk": client.user.pk},
    )


def test_cleanup_forbidden_for_collaborator(db):
    client = CollaboratorAuthClient()
    assert client.get(cleanup_url()).status_code == 403


def test_cleanup_without_orphans_redirects_with_message(db):
    client = PowerUserAuthClient()
    response = client.get(cleanup_url())
    assert response.status_code == 302
    assert response.url == overview_url()
    assert [m.level_tag for m in get_messages(response.wsgi_request)] == ["success"]


def make_orphan(canton):
    user = UserFactory(first_name="Orphan", profile__affiliation_canton=canton)
    QualificationFactory(
        actor=user,
        session=SessionFactory(
            day=DAY, orga=OrganizationFactory(address_canton=canton)
        ),
    )
    TimesheetFactory(user=user, date=DAY)
    return TimesheetFactory(user=user, date=DAY + datetime.timedelta(days=1))


@pytest.fixture
def orphan(db):
    return make_orphan("VS")


def test_cleanup_lists_orphaned_timesheets(orphan):
    client = PowerUserAuthClient()
    response = client.get(cleanup_url())
    assert response.status_code == 200
    assert response.context["orphaned_timesheets"] == {orphan}
    assert response.context["redirect_url"] == overview_url()
    assert response.context["period"] == "avril 2019"


def test_cleanup_post_deletes_only_orphans(orphan):
    client = PowerUserAuthClient()
    response = client.post(cleanup_url())
    assert response.status_code == 302
    assert response.url == overview_url()
    assert list(Timesheet.objects.values_list("date", flat=True)) == [DAY]
    messages = [str(m) for m in get_messages(response.wsgi_request)]
    assert messages == ["1 feuille d'heures orpheline supprimée."]


def test_cleanup_state_manager_ignores_other_cantons(orphan):
    client = StateManagerAuthClient()
    response = client.get(cleanup_url())
    assert response.status_code == 302
    assert Timesheet.objects.count() == 2


@pytest.mark.xfail(
    strict=True,
    reason=(
        "CleanupOrphanedTimesheets checks `active_canton in DV_STATE_CHOICES` "
        "(a list of tuples) so the canton filter is always ignored"
    ),
)
def test_cleanup_honours_canton_filter(orphan):
    vd_orphan = make_orphan("VD")
    client = PowerUserAuthClient()
    response = client.get(cleanup_url() + "?canton=VD")
    assert response.status_code == 200
    assert response.context["orphaned_timesheets"] == {vd_orphan}


def test_yearly_overview_canton_filter(db):
    vd_user = UserFactory(first_name="Vaudois", profile__affiliation_canton="VD")
    vs_user = UserFactory(first_name="Valaisan", profile__affiliation_canton="VS")
    QualificationFactory(
        actor=vd_user,
        session=SessionFactory(day=DAY, orga=OrganizationFactory(address_canton="VD")),
    )
    QualificationFactory(
        actor=vs_user,
        session=SessionFactory(day=DAY, orga=OrganizationFactory(address_canton="VS")),
    )
    TimesheetFactory(user=vs_user, date=DAY, time_helper=4)

    client = PowerUserAuthClient()
    response = client.get(overview_url() + "?canton=VD")

    assert response.status_code == 200
    assert list(response.context["timesheets_status_matrix"]) == [vd_user]
    assert response.context["active_canton"] == "Vaud"
    assert response.context["timesheets_amount"] == [0] * 12
    assert response.context["show_reminder_button_months"][3] is True


def test_yearly_overview_forbidden_without_timesheet_permission(db):
    assert AuthClient().get(overview_url()).status_code == 403


def test_regroup_sessions_by_user_includes_leaders_and_helpers(db):
    leader, helper, outsider = UserFactory(), UserFactory(), UserFactory()
    session = SessionFactory(day=DAY)
    QualificationFactory(session=session, leader=leader, helpers=[helper, outsider])

    sessions = timesheets_overview.regroup_sessions_by_user([session], [leader, helper])

    assert sessions == {leader.pk: {session}, helper.pk: {session}}


def test_orphaned_timesheets_skip_users_without_profile(db):
    user = get_user_model().objects.create(username="noprofile")
    TimesheetFactory(user=user, date=DAY)

    result = timesheets_overview.get_orphaned_timesheets_per_month(
        year=2019, users=get_user_model().objects.filter(pk=user.pk), month=4
    )

    assert result == set()
