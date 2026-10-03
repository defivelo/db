import datetime

from django.core import mail
from django.urls import reverse

import pytest

from apps.common import (
    DV_SEASON_AUTUMN,
    DV_SEASON_SPRING,
    DV_SEASON_STATE_ARCHIVED,
    DV_SEASON_STATE_OPEN,
    DV_SEASON_STATE_PLANNING,
    DV_SEASON_STATE_RUNNING,
    DV_STATES,
)
from apps.orga.tests.factories import OrganizationFactory
from apps.user import FORMATION_M1, FORMATION_M2
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import (
    CollaboratorAuthClient,
    CoordinatorAuthClient,
    PowerUserAuthClient,
    StateManagerAuthClient,
)

from .. import (
    AVAILABILITY_FIELDKEY,
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
    SEASON_WORKWISH_FIELDKEY,
    STAFF_FIELDKEY,
    SUPERLEADER_FIELDKEY,
)
from ..forms.season import SeasonStaffChoiceForm, SeasonStaffFilterForm
from ..models import HelperSessionAvailability
from ..models.availability import HelperSeasonWorkWish
from ..views.season import GeneralPlanningSupportMixin, SeasonExportView
from .factories import (
    QualificationActivityFactory,
    QualificationFactory,
    SeasonFactory,
    SessionFactory,
)

CANTON = DV_STATES[0]
OTHER_CANTON = DV_STATES[1]
YEAR = 2024


def make_season(state=DV_SEASON_STATE_OPEN, cantons=None, month_start=3, **kwargs):
    return SeasonFactory(
        year=YEAR,
        month_start=month_start,
        n_months=1,
        cantons=cantons or [CANTON],
        state=state,
        **kwargs,
    )


def make_session(season, canton=CANTON, day_offset=0, **kwargs):
    return SessionFactory(
        orga__address_canton=canton,
        orga__address_city="Lausanne",
        day=season.begin + datetime.timedelta(days=day_offset),
        begin=datetime.time(8, 30),
        duration=datetime.timedelta(hours=4),
        **kwargs,
    )


def make_helper(formation=FORMATION_M1, canton=CANTON, **kwargs):
    return UserFactory(
        profile__formation=formation,
        profile__affiliation_canton=canton,
        **kwargs,
    )


def helper_client(canton=CANTON, formation=FORMATION_M1):
    client = CollaboratorAuthClient()
    client.user.profile.affiliation_canton = canton
    client.user.profile.formation = formation
    client.user.profile.save()
    return client


@pytest.fixture
def season(db):
    return make_season()


@pytest.fixture
def session(season):
    session = make_session(season)
    QualificationFactory(session=session)
    return session


@pytest.fixture
def state_manager(db):
    return StateManagerAuthClient()


@pytest.fixture
def power_user(db):
    return PowerUserAuthClient()


class TestSeasonList:
    def url(self, dv_season):
        return reverse("season-list", kwargs={"year": YEAR, "dv_season": dv_season})

    @pytest.mark.parametrize("dv_season", [2, 4])
    def test_unknown_dv_season_is_forbidden(self, state_manager, dv_season):
        assert state_manager.get(self.url(dv_season)).status_code == 403

    def test_spring_lists_only_spring_seasons(self, state_manager):
        spring = make_season(month_start=3)
        autumn = make_season(month_start=10)
        response = state_manager.get(self.url(DV_SEASON_SPRING))
        assert response.status_code == 200
        assert list(response.context["seasons"]) == [spring]
        assert autumn not in response.context["seasons"]
        assert response.context["dv_season_prev_day"] == datetime.date(YEAR - 1, 8, 1)
        assert response.context["dv_season_next_day"] == datetime.date(YEAR, 8, 1)

    def test_autumn_lists_only_autumn_seasons(self, state_manager):
        make_season(month_start=3)
        autumn = make_season(month_start=10)
        response = state_manager.get(self.url(DV_SEASON_AUTUMN))
        assert list(response.context["seasons"]) == [autumn]
        assert response.context["dv_season_prev_day"] == datetime.date(YEAR, 1, 1)
        assert response.context["dv_season_next_day"] == datetime.date(YEAR + 1, 1, 1)


class TestSeasonDetail:
    def test_unknown_season_is_404(self, state_manager):
        url = reverse("season-detail", kwargs={"pk": 999999})
        assert state_manager.get(url).status_code == 404

    def test_selected_helper_can_see_running_season(self, db):
        season = make_season(state=DV_SEASON_STATE_RUNNING)
        session = make_session(season)
        client = helper_client()
        QualificationFactory(session=session, helpers=[client.user])
        response = client.get(reverse("season-detail", kwargs={"pk": season.pk}))
        assert response.status_code == 200

    def test_coordinator_only_sees_own_organization_sessions(self, season):
        client = CoordinatorAuthClient()
        own = make_session(season, orga__coordinator=client.user)
        QualificationFactory(session=own)
        other = make_session(season)
        QualificationFactory(session=other)
        response = client.get(reverse("season-detail", kwargs={"pk": season.pk}))
        assert response.status_code == 200
        assert list(response.context["sessions_by_orga"]) == [own]


class TestSeasonHelperList:
    def test_collaborator_without_cantons_is_forbidden(self, season):
        client = CollaboratorAuthClient()
        url = reverse("season-helperlist", kwargs={"pk": season.pk})
        assert client.get(url).status_code == 403

    def test_season_leader_outside_managed_cantons_is_forbidden(self, db):
        client = StateManagerAuthClient()
        season = make_season(cantons=[OTHER_CANTON], leader=client.user)
        url = reverse("season-helperlist", kwargs={"pk": season.pk})
        assert client.get(url).status_code == 403

    def test_lists_qualification_helpers(self, state_manager, season, session):
        leader = make_helper(formation=FORMATION_M2)
        helper = make_helper()
        bystander = make_helper()
        QualificationFactory(session=session, leader=leader, helpers=[helper])
        url = reverse("season-helperlist", kwargs={"pk": season.pk})
        response = state_manager.get(url)
        assert response.status_code == 200
        users = set(response.context["users"])
        assert {leader, helper} <= users
        assert bystander not in users


class TestSeasonToRunning:
    def test_post_sends_email_to_season_helpers(self, state_manager, season, session):
        available = make_helper()
        unavailable = make_helper()
        HelperSessionAvailability.objects.create(
            session=session, helper=available, availability="y"
        )
        HelperSessionAvailability.objects.create(
            session=session, helper=unavailable, availability="n"
        )
        url = reverse("season-set-running", kwargs={"pk": season.pk})
        response = state_manager.post(
            url,
            {
                "state": DV_SEASON_STATE_RUNNING,
                "sendemail": "on",
                "customtext": "Texte spécial",
            },
        )
        assert response.status_code == 302
        season.refresh_from_db()
        assert season.state == DV_SEASON_STATE_RUNNING
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to[0].endswith(f"<{available.email}>")
        assert "Texte spécial" in mail.outbox[0].body
        planning_url = reverse(
            "season-planning", kwargs={"pk": season.pk, "helperpk": available.pk}
        )
        assert planning_url in mail.outbox[0].body

    def test_post_without_sendemail_sends_nothing(self, state_manager, season, session):
        helper = make_helper()
        HelperSessionAvailability.objects.create(
            session=session, helper=helper, availability="y"
        )
        url = reverse("season-set-running", kwargs={"pk": season.pk})
        response = state_manager.post(url, {"state": DV_SEASON_STATE_RUNNING})
        assert response.status_code == 302
        assert mail.outbox == []


class TestSeasonToOpen:
    def test_post_sends_email_to_active_helpers_of_cantons(self, state_manager, db):
        season = make_season(state=DV_SEASON_STATE_PLANNING)
        local = make_helper()
        make_helper(canton=OTHER_CANTON)
        make_helper(formation="")
        url = reverse("season-set-open", kwargs={"pk": season.pk})
        response = state_manager.post(
            url,
            {"state": DV_SEASON_STATE_OPEN, "sendemail": "on", "customtext": "Hop"},
        )
        assert response.status_code == 302
        season.refresh_from_db()
        assert season.state == DV_SEASON_STATE_OPEN
        assert len(mail.outbox) == 1
        assert local.email in mail.outbox[0].to[0]
        update_url = reverse(
            "season-availabilities-update",
            kwargs={"pk": season.pk, "helperpk": local.pk},
        )
        assert update_url in mail.outbox[0].body
        assert "Hop" in mail.outbox[0].body


class TestSeasonAvailabilityReminder:
    def test_no_sessions_means_no_recipients(self, state_manager, season):
        make_helper()
        url = reverse("season-availability-reminder", kwargs={"pk": season.pk})
        response = state_manager.get(url)
        assert response.status_code == 200
        assert response.context["recipients"] == []

    def test_post_without_sendemail_does_not_mark_sent(
        self, state_manager, season, session
    ):
        make_helper()
        url = reverse("season-availability-reminder", kwargs={"pk": season.pk})
        response = state_manager.post(url, {})
        assert response.status_code == 302
        season.refresh_from_db()
        assert season.availability_reminder_sent_at is None
        assert mail.outbox == []


class TestSeasonExport:
    def test_undetected_translations(self):
        assert [str(s) for s in SeasonExportView().undetected_translations()] == [
            "Int.",
            "M+",
        ]

    @pytest.mark.parametrize("fmt", ["csv", "ods", "xls"])
    def test_export_formats(self, state_manager, season, session, fmt):
        url = reverse("season-export", kwargs={"pk": season.pk, "format": fmt})
        response = state_manager.get(url)
        assert response.status_code == 200
        assert "attachment" in response["Content-Disposition"]
        assert response["Content-Disposition"].endswith(f'.{fmt}"')

    def test_csv_contains_staff_and_empty_sessions(self, state_manager, season):
        session = make_session(season)
        superleader = make_helper(formation=FORMATION_M2)
        session.superleader = superleader
        session.save()
        leader = make_helper(formation=FORMATION_M2)
        helper1 = make_helper()
        helper2 = make_helper()
        QualificationFactory(session=session, leader=leader, helpers=[helper1, helper2])
        empty_session = make_session(season, day_offset=1)
        url = reverse("season-export", kwargs={"pk": season.pk, "format": "csv"})
        content = state_manager.get(url).content.decode()
        for user in (superleader, leader, helper1, helper2):
            assert user.get_full_name() in content
        assert empty_session.orga.name in content


class TestGeneralPlanningSupportMixin:
    def make_view(self, **kwargs):
        view = GeneralPlanningSupportMixin()
        view.kwargs = kwargs
        return view

    def test_invalid_scope_returns_empty(self):
        assert self.make_view(year="x", dv_season="1")._seasons_in_scope() == (
            None,
            None,
            [],
        )

    def test_invalid_helperpk_is_none(self):
        assert self.make_view(helperpk="abc")._helperpk_in_kwargs() is None
        assert self.make_view()._helperpk_in_kwargs() is None
        assert self.make_view(helperpk="12")._helperpk_in_kwargs() == 12


def general_kwargs(helperpk, **extra):
    return {"year": YEAR, "dv_season": DV_SEASON_SPRING, "helperpk": helperpk, **extra}


class TestPersonalPlanningExport:
    def test_planning_export_lists_all_season_people(
        self, state_manager, season, session
    ):
        helper = make_helper()
        QualificationFactory(session=session, helpers=[helper])
        url = reverse(
            "season-planning-export", kwargs={"pk": season.pk, "format": "csv"}
        )
        response = state_manager.get(url)
        assert response.status_code == 200
        assert helper.get_full_name() in response.content.decode()

    def test_general_export_allowed_for_helper_when_running(self, db):
        season = make_season(state=DV_SEASON_STATE_RUNNING)
        session = make_session(season)
        client = helper_client()
        QualificationFactory(session=session, helpers=[client.user])
        url = reverse(
            "season-personal-planning-export",
            kwargs=general_kwargs(client.user.pk, format="csv"),
        )
        response = client.get(url)
        assert response.status_code == 200
        assert session.orga.name in response.content.decode()

    def test_general_export_forbidden_for_helper_when_not_running(self, season):
        client = helper_client()
        url = reverse(
            "season-personal-planning-export",
            kwargs=general_kwargs(client.user.pk, format="csv"),
        )
        assert client.get(url).status_code == 403

    def test_general_export_without_assignment_has_no_session(
        self, state_manager, season, session
    ):
        helper = make_helper()
        HelperSessionAvailability.objects.create(
            session=session, helper=helper, availability="y", chosen_as=CHOSEN_AS_NOT
        )
        superleader_session = make_session(season, superleader=helper)
        QualificationFactory(session=superleader_session)
        url = reverse(
            "season-personal-planning-export",
            kwargs=general_kwargs(helper.pk, format="csv"),
        )
        response = state_manager.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert helper.get_full_name() in content
        assert superleader_session.orga.name not in content

    def test_month_export_forbidden_for_foreign_helper(self, season, session):
        client = helper_client(canton=OTHER_CANTON)
        url = reverse(
            "season-personal-planning-export",
            kwargs={"pk": season.pk, "helperpk": client.user.pk, "format": "csv"},
        )
        assert client.get(url).status_code == 403


class TestSeasonAvailabilityView:
    def test_lists_current_availabilities(self, state_manager, season, session):
        helper = make_helper()
        HelperSessionAvailability.objects.create(
            session=session, helper=helper, availability="i"
        )
        url = reverse("season-availabilities", kwargs={"pk": season.pk})
        response = state_manager.get(url)
        assert response.status_code == 200
        key = AVAILABILITY_FIELDKEY.format(hpk=helper.pk, spk=session.pk)
        assert response.context["availabilities"][key] == "i"
        m1_helpers = dict(
            (str(k), list(v)) for k, v in response.context["potential_helpers"]
        )
        assert helper in m1_helpers["Moniteur·trice·s 1"]

    def test_post_valid_helper_redirects_to_update(self, state_manager, season):
        helper = make_helper()
        url = reverse("season-availabilities", kwargs={"pk": season.pk})
        response = state_manager.post(url, {"helper": helper.pk})
        assert response.status_code == 302
        assert response.url == reverse(
            "season-availabilities-update",
            kwargs={"pk": season.pk, "helperpk": helper.pk},
        )

    def test_post_invalid_helper_redirects_back(self, state_manager, season):
        url = reverse("season-availabilities", kwargs={"pk": season.pk})
        response = state_manager.post(url, {"helper": ""})
        assert response.status_code == 302
        assert response.url == url


class TestSeasonPlanningView:
    def test_helperpk_zero_redirects_to_own_planning(self, state_manager, season):
        url = reverse("season-planning", kwargs={"pk": season.pk, "helperpk": 0})
        response = state_manager.get(url)
        assert response.status_code == 302
        assert response.url == reverse(
            "season-planning",
            kwargs={"pk": season.pk, "helperpk": state_manager.user.pk},
        )


class TestSeasonGeneralPlanningView:
    def url(self, helperpk):
        return reverse("season-general-planning", kwargs=general_kwargs(helperpk))

    def test_helper_sees_running_general_planning(self, db):
        season = make_season(state=DV_SEASON_STATE_RUNNING)
        session = make_session(season)
        client = helper_client()
        QualificationFactory(session=session, helpers=[client.user])
        response = client.get(self.url(client.user.pk))
        assert response.status_code == 200
        assert list(response.context["sessions"]) == [session]
        assert response.context["user_can_see_season"] is True

    def test_helper_redirected_to_availabilities_when_open(self, season, session):
        client = helper_client()
        response = client.get(self.url(client.user.pk))
        assert response.status_code == 302
        assert response.url == reverse(
            "season-availabilities-update",
            kwargs={"pk": season.pk, "helperpk": client.user.pk},
        )

    def test_helper_forbidden_when_planning(self, db):
        make_season(state=DV_SEASON_STATE_PLANNING)
        client = helper_client()
        assert client.get(self.url(client.user.pk)).status_code == 403

    def test_manager_without_availabilities_gets_empty_planning(
        self, state_manager, season, session
    ):
        response = state_manager.get(self.url(state_manager.user.pk))
        assert response.status_code == 200
        assert len(response.context["availabilities"]) == 0
        assert list(response.context["sessions"]) == []


class TestSeasonAvailabilityUpdate:
    def url(self, season, helper):
        return reverse(
            "season-availabilities-update",
            kwargs={"pk": season.pk, "helperpk": helper.pk},
        )

    def test_manager_post_creates_and_updates_records(
        self, state_manager, season, session
    ):
        other_session = make_session(season, day_offset=1)
        QualificationFactory(session=other_session)
        helper = make_helper()
        HelperSessionAvailability.objects.create(
            session=session, helper=helper, availability="n"
        )
        HelperSeasonWorkWish.objects.create(season=season, helper=helper, amount=1)
        data = {
            SEASON_WORKWISH_FIELDKEY.format(hpk=helper.pk): 3,
            AVAILABILITY_FIELDKEY.format(hpk=helper.pk, spk=session.pk): "y",
            AVAILABILITY_FIELDKEY.format(hpk=helper.pk, spk=other_session.pk): "i",
        }
        response = state_manager.post(self.url(season, helper), data)
        assert response.status_code == 302
        assert response.url == reverse(
            "season-availabilities", kwargs={"pk": season.pk}
        )
        assert (
            HelperSeasonWorkWish.objects.get(season=season, helper=helper).amount == 3
        )
        availabilities = dict(
            HelperSessionAvailability.objects.filter(helper=helper).values_list(
                "session_id", "availability"
            )
        )
        assert availabilities == {session.pk: "y", other_session.pk: "i"}

    def test_post_with_duplicate_work_wishes_updates_latest(
        self, state_manager, season, session
    ):
        helper = make_helper()
        HelperSeasonWorkWish.objects.create(season=season, helper=helper, amount=1)
        latest = HelperSeasonWorkWish.objects.create(
            season=season, helper=helper, amount=1
        )
        data = {SEASON_WORKWISH_FIELDKEY.format(hpk=helper.pk): 5}
        response = state_manager.post(self.url(season, helper), data)
        assert response.status_code == 302
        latest.refresh_from_db()
        assert latest.amount == 5

    def test_helper_post_redirects_to_own_update(self, season, session):
        client = helper_client()
        data = {
            SEASON_WORKWISH_FIELDKEY.format(hpk=client.user.pk): 2,
            AVAILABILITY_FIELDKEY.format(hpk=client.user.pk, spk=session.pk): "y",
        }
        response = client.post(self.url(season, client.user), data)
        assert response.status_code == 302
        assert response.url == self.url(season, client.user)
        assert (
            HelperSessionAvailability.objects.get(
                session=session, helper=client.user
            ).availability
            == "y"
        )
        assert (
            HelperSeasonWorkWish.objects.get(season=season, helper=client.user).amount
            == 2
        )

    def test_manager_cannot_update_archived_season(self, state_manager):
        season = make_season(state=DV_SEASON_STATE_ARCHIVED)
        helper = make_helper()
        assert state_manager.get(self.url(season, helper)).status_code == 403


class TestSeasonStaffChoiceUpdate:
    def url(self, season):
        return reverse("season-staff-update", kwargs={"pk": season.pk})

    def test_get_without_sessions_hides_organisation_filter(
        self, state_manager, season
    ):
        response = state_manager.get(self.url(season))
        assert response.status_code == 200
        filter_form = response.context["season_staff_filter_form"]
        assert "organisations" not in filter_form.fields

    def test_get_builds_initial_for_partial_availabilities(
        self, state_manager, season, session
    ):
        other_session = make_session(season, day_offset=1)
        QualificationFactory(session=other_session)
        helper = make_helper(formation=FORMATION_M2)
        session.superleader = helper
        session.save()
        HelperSessionAvailability.objects.create(
            session=session, helper=helper, availability="y", chosen_as=CHOSEN_AS_LEADER
        )
        response = state_manager.get(self.url(season))
        assert response.status_code == 200
        initial = response.context["availabilities"]
        assert initial[STAFF_FIELDKEY.format(hpk=helper.pk, spk=session.pk)] == (
            CHOSEN_AS_LEADER
        )
        assert initial[STAFF_FIELDKEY.format(hpk=helper.pk, spk=other_session.pk)] == ""
        assert (
            initial[SUPERLEADER_FIELDKEY.format(hpk=helper.pk, spk=session.pk)] is True
        )
        form = response.context["form"]
        field = form.fields[STAFF_FIELDKEY.format(hpk=helper.pk, spk=session.pk)]
        assert CHOSEN_AS_LEADER in [c[0] for c in field.choices]
        filter_form = response.context["season_staff_filter_form"]
        assert {c[0] for c in filter_form.fields["organisations"].choices} == {
            session.orga.pk,
            other_session.orga.pk,
        }

    def test_post_updates_choices_and_drops_unchosen_staff(
        self, state_manager, season, session
    ):
        leader = make_helper(formation=FORMATION_M2)
        helper = make_helper()
        quali = QualificationFactory(session=session, leader=leader, helpers=[helper])
        data = {
            STAFF_FIELDKEY.format(hpk=leader.pk, spk=session.pk): CHOSEN_AS_NOT,
            STAFF_FIELDKEY.format(hpk=helper.pk, spk=session.pk): CHOSEN_AS_HELPER,
        }
        response = state_manager.post(self.url(season), data)
        assert response.status_code == 302
        assert response.url == reverse(
            "season-availabilities", kwargs={"pk": season.pk}
        )
        quali.refresh_from_db()
        assert quali.leader is None
        assert list(quali.helpers.all()) == [helper]
        assert (
            HelperSessionAvailability.objects.get(
                session=session, helper=leader
            ).chosen_as
            == CHOSEN_AS_NOT
        )

    def test_post_drops_unchosen_actor(self, state_manager, season, session):
        actor = make_helper(formation="")
        actor.profile.actor_for.add(QualificationActivityFactory(category="C"))
        quali = QualificationFactory(session=session, actor=actor)
        data = {STAFF_FIELDKEY.format(hpk=actor.pk, spk=session.pk): CHOSEN_AS_NOT}
        state_manager.post(self.url(season), data)
        quali.refresh_from_db()
        assert quali.actor is None

    @pytest.mark.xfail(
        reason="SeasonStaffChoiceUpdateView.form_valid removes the loop's last "
        "`helper` instead of `non_helper` from quali.helpers",
        strict=True,
    )
    def test_post_removes_the_unchosen_m1_only(self, state_manager, season, session):
        dropped = make_helper(first_name="Aaa")
        kept = make_helper(first_name="Zzz")
        quali = QualificationFactory(session=session, helpers=[dropped, kept])
        data = {
            STAFF_FIELDKEY.format(hpk=dropped.pk, spk=session.pk): CHOSEN_AS_NOT,
            STAFF_FIELDKEY.format(hpk=kept.pk, spk=session.pk): CHOSEN_AS_HELPER,
        }
        state_manager.post(self.url(season), data)
        assert list(quali.helpers.all()) == [kept]

    def test_post_with_empty_choice_keeps_availability(
        self, state_manager, season, session
    ):
        helper = make_helper()
        HelperSessionAvailability.objects.create(
            session=session, helper=helper, availability="y", chosen_as=CHOSEN_AS_HELPER
        )
        data = {STAFF_FIELDKEY.format(hpk=helper.pk, spk=session.pk): ""}
        response = state_manager.post(self.url(season), data)
        assert response.status_code == 302
        assert (
            HelperSessionAvailability.objects.get(
                session=session, helper=helper
            ).chosen_as
            == CHOSEN_AS_HELPER
        )

    def test_form_offers_actor_and_helper_choices(self, season, session):
        helper = make_helper()
        helper.profile.actor_for.add(QualificationActivityFactory(category="C"))
        form = SeasonStaffChoiceForm(
            instance=season, available_helpers=[("M1", [helper])]
        )
        field = form.fields[STAFF_FIELDKEY.format(hpk=helper.pk, spk=session.pk)]
        assert [c[0] for c in field.choices] == [
            CHOSEN_AS_NOT,
            CHOSEN_AS_ACTOR,
            CHOSEN_AS_REPLACEMENT,
            CHOSEN_AS_HELPER,
        ]
        assert field.initial == CHOSEN_AS_NOT

    def test_form_save_is_noop(self, season):
        form = SeasonStaffChoiceForm(instance=season, available_helpers=None)
        assert form.save() is None
        assert form.fields == {}

    def test_filter_form_sorts_organisations(self, db):
        b = OrganizationFactory(name="Bbb", abbr="")
        a = OrganizationFactory(name="Aaa", abbr="")
        form = SeasonStaffFilterForm(organisations=[b, a])
        assert [c[0] for c in form.fields["organisations"].choices] == [a.pk, b.pk]


class TestSeasonErrorsList:
    def test_lists_only_incoherent_qualifications(self, state_manager, season, session):
        leader = make_helper(formation=FORMATION_M2)
        coherent = QualificationFactory(session=session, leader=leader)
        incoherent = QualificationFactory(session=session)
        incoherent.helpers.add(make_helper())
        url = reverse("season-errorslist", kwargs={"pk": season.pk})
        response = state_manager.get(url)
        assert response.status_code == 200
        assert response.context["submenu_category"] == "season-errorslist"
        assert list(response.context["qualifs"]) == [incoherent]
        assert coherent not in response.context["qualifs"]


class TestPersonalCalendarFeed:
    def test_month_feed_lists_assigned_sessions(self, state_manager, season):
        helper = make_helper()
        session = make_session(season)
        QualificationFactory(session=session, helpers=[helper])
        unassigned = make_session(season, day_offset=1)
        QualificationFactory(session=unassigned)
        url = reverse(
            "season-personal-calendar",
            kwargs={"pk": season.pk, "helperpk": helper.pk},
        )
        response = state_manager.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert content.count("BEGIN:VEVENT") == 1
        assert f"UID:{session.pk}-session" in content
        assert session.orga.name in content
        assert "Lausanne" in content
        assert "DTSTART:" in content
        assert (
            reverse("season-planning", kwargs={"pk": season.pk, "helperpk": helper.pk})
            in content
        )

    def test_general_feed_links_to_general_planning(self, db):
        season = make_season(state=DV_SEASON_STATE_RUNNING)
        session = make_session(season, place="Préau")
        client = helper_client()
        QualificationFactory(session=session, helpers=[client.user])
        url = reverse("season-personal-calendar", kwargs=general_kwargs(client.user.pk))
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Préau" in content
        general_url = reverse(
            "season-general-planning", kwargs=general_kwargs(client.user.pk)
        )
        assert general_url in content.replace("\r\n ", "")

    def test_general_feed_forbidden_when_not_running(self, season):
        client = helper_client()
        url = reverse("season-personal-calendar", kwargs=general_kwargs(client.user.pk))
        assert client.get(url).status_code == 403

    @pytest.mark.xfail(
        strict=True,
        reason="Bug: the per-season feed has no access control, anyone logged in "
        "can read any helper's sessions",
    )
    def test_month_feed_forbidden_for_outsider(self, season):
        helper = make_helper()
        session = make_session(season)
        QualificationFactory(session=session, helpers=[helper])
        outsider = helper_client(canton=OTHER_CANTON)
        url = reverse(
            "season-personal-calendar",
            kwargs={"pk": season.pk, "helperpk": helper.pk},
        )
        response = outsider.get(url)
        assert response.status_code == 403
