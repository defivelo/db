# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016, 2020 Didier Raboud <me+defivelo@odyx.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import datetime

from django.test import TestCase
from django.urls import reverse

from apps.common import (
    DV_SEASON_STATE_ARCHIVED,
    DV_SEASON_STATE_OPEN,
    DV_SEASON_STATE_PLANNING,
    DV_SEASON_STATE_RUNNING,
    DV_SEASON_STATES,
    DV_STATES,
)
from apps.common.forms import SWISS_DATE_INPUT_FORMAT
from apps.orga.tests.factories import OrganizationFactory
from apps.user import FORMATION_M1
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import (
    AuthClient,
    CoordinatorAuthClient,
    PowerUserAuthClient,
    StateManagerAuthClient,
)

from .factories import QualificationFactory, SeasonFactory, SessionFactory

freeforallurls = ["season-list"]
restrictedgenericurls = ["season-create"]
restrictedspecificurls = [
    "season-detail",
    "season-update",
    "season-helperlist",
    "season-actorlist",
    "season-availabilities",
    "season-staff-update",
    "season-set-running",
    "season-set-open",
]
restrictedhelperspecificurls = [
    "season-availabilities-update",
    "season-planning",
]


class SeasonTestCaseMixin(TestCase):
    def setUp(self):
        self.users = [UserFactory() for i in range(3)]

        self.season = SeasonFactory()
        self.mycantons = [c.canton for c in self.client.user.managedstates.all()]
        if self.mycantons:
            self.season.cantons = self.mycantons
        else:
            self.season.cantons = [
                DV_STATES[0],
            ]
        self.season.save()

        self.sessions = []
        self.canton_orgas = []
        for canton in self.season.cantons:
            s = SessionFactory()
            s.orga.address_canton = canton
            s.orga.save()
            self.canton_orgas.append(s.orga)
            s.day = self.season.begin
            s.save()
            for i in range(0, 4):
                QualificationFactory(session=s)
            self.sessions.append(s)

        self.foreigncantons = [c for c in DV_STATES if c not in self.mycantons]
        self.foreignseason = SeasonFactory(cantons=self.foreigncantons)

        self.foreignsessions = []
        for canton in self.foreigncantons:
            s = SessionFactory()
            s.orga.address_canton = canton
            s.orga.save()
            s.day = self.foreignseason.begin
            s.save()
            for i in range(0, 4):
                QualificationFactory(session=s)
            self.foreignsessions.append(s)


class AuthUserTest(SeasonTestCaseMixin):
    def setUp(self):
        self.client = AuthClient()
        super(AuthUserTest, self).setUp()

    def test_access_to_season_list(self):
        for symbolicurl in freeforallurls:
            url = reverse(symbolicurl)
            # Final URL is OK
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)

    def test_no_access_to_season_create(self):
        for symbolicurl in restrictedgenericurls:
            url = reverse(symbolicurl)
            # Final URL is forbidden
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 403, url)

    def test_no_access_to_season_detail(self):
        for symbolicurl in restrictedspecificurls:
            url = reverse(symbolicurl, kwargs={"pk": self.season.pk})
            # Final URL is forbidden
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 403, url)
        for symbolicurl in restrictedhelperspecificurls:
            for helper in self.users:
                url = reverse(
                    symbolicurl, kwargs={"pk": self.season.pk, "helperpk": helper.pk}
                )
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 403, url)

    def test_access_to_myseason_availabilities(self):
        urls = {
            symbolicurl: reverse(
                symbolicurl,
                kwargs={"pk": self.season.pk, "helperpk": self.client.user.pk},
            )
            for symbolicurl in restrictedhelperspecificurls
        }
        # Fails, we have no formation
        for k, url in urls.items():
            self.assertEqual(self.client.get(url).status_code, 403, url)

        # Fails, we have not a common canton
        self.client.user.profile.formation = FORMATION_M1
        self.client.user.profile.save()
        for k, url in urls.items():
            self.assertEqual(self.client.get(url).status_code, 403, url)

        # Works, we have it all
        self.client.user.profile.affiliation_canton = self.season.cantons[0]
        self.client.user.profile.save()
        response = self.client.get(urls["season-availabilities-update"])
        self.assertEqual(response.status_code, 200, ["season-availabilities-update"])
        self.assertTemplateUsed(response, "widgets/BSRadioSelect_option.html")

        # If, by mistake, the user got sent a url with a helperpk set to 0, it will redirect
        response = self.client.get(
            reverse(
                "season-availabilities-update",
                kwargs={"pk": self.season.pk, "helperpk": 0},
            )
        )
        self.assertEqual(
            response.status_code,
            302,
            "DEFIVELO-221: Availabilities' update URL with helperpk set to 0",
        )

        # The season is not open
        for state in DV_SEASON_STATES:
            self.season.state = state[0]
            self.season.save()
            response = self.client.get(urls["season-availabilities-update"])
            if state[0] == DV_SEASON_STATE_OPEN:
                self.assertEqual(
                    response.status_code, 200, urls["season-availabilities-update"]
                )
            elif state[0] == DV_SEASON_STATE_RUNNING:
                # When possible, we redirect to planning
                self.assertEqual(
                    response.status_code, 302, urls["season-availabilities-update"]
                )
            else:
                self.assertEqual(
                    response.status_code, 403, urls["season-availabilities-update"]
                )
        # Test the access to the planning
        for state in DV_SEASON_STATES:
            self.season.state = state[0]
            self.season.save()
            response = self.client.get(urls["season-planning"])
            if state[0] == DV_SEASON_STATE_RUNNING:
                # … We can see the season
                self.assertEqual(response.status_code, 200, urls["season-planning"])
                for exportformat in ["csv", "ods", "xls"]:
                    url = reverse(
                        "season-personal-planning-export",
                        kwargs={
                            "pk": self.season.pk,
                            "helperpk": self.client.user.pk,
                            "format": exportformat,
                        },
                    )
                    response = self.client.get(url, follow=True)
                    self.assertEqual(response.status_code, 200, url)
                url = reverse(
                    "season-personal-calendar",
                    kwargs={"pk": self.season.pk, "helperpk": self.client.user.pk},
                )
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)
            elif state[0] == DV_SEASON_STATE_OPEN:
                # When possible, we redirect to availabilities
                self.assertEqual(response.status_code, 302, urls["season-planning"])
            else:
                self.assertEqual(response.status_code, 403, urls["season-planning"])

        self.season.state = DV_SEASON_STATE_OPEN
        self.season.save()

        # Fails, we have a common canton, but no Formation
        self.client.user.profile.formation = ""
        self.client.user.profile.save()
        for k, url in urls.items():
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_access_to_sessions(self):
        # Make this user a M1 from this season's cantons
        self.client.user.profile.formation = FORMATION_M1
        self.client.user.profile.affiliation_canton = self.season.cantons[0]
        self.client.user.profile.save()

        # Test the access to the session on all season states
        for state in DV_SEASON_STATES:
            self.season.state = state[0]
            self.season.save()
            for session in self.sessions:
                session_kwargs = {
                    "seasonpk": self.season.pk,
                    "pk": session.pk,
                }
                weeklysessionlist = reverse(
                    "session-list",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "year": session.day.year,
                        "week": session.day.strftime("%W"),
                    },
                )
                urls = [
                    weeklysessionlist,
                    reverse(
                        "session-create",
                        kwargs={
                            "seasonpk": self.season.pk,
                        },
                    ),
                    reverse(
                        "session-detail",
                        kwargs=session_kwargs,
                    ),
                    reverse(
                        "session-update",
                        kwargs=session_kwargs,
                    ),
                    reverse(
                        "session-staff-choices",
                        kwargs=session_kwargs,
                    ),
                    reverse(
                        "session-delete",
                        kwargs=session_kwargs,
                    ),
                ]
                for url in urls:
                    # Final URL is forbidden
                    response = self.client.get(url, follow=True)
                    self.assertEqual(response.status_code, 403, url)
                # Now add user to a Qualif of that Session
                q = session.qualifications.first()
                q.helpers.add(self.client.user)
                # Recheck all URLs
                for url in urls:
                    # Loop through the two cases
                    for visible in [True, False]:
                        session.visible = visible
                        session.save()
                        response = self.client.get(url, follow=True)
                        # When the season is running, we can access some stuff
                        if state[0] == DV_SEASON_STATE_RUNNING and (
                            url == weeklysessionlist
                            or (
                                visible
                                and url
                                in [
                                    reverse(
                                        "session-detail",
                                        kwargs=session_kwargs,
                                    ),
                                    reverse(
                                        "session-staff-choices",
                                        kwargs=session_kwargs,
                                    ),
                                ]
                            )
                        ):
                            self.assertEqual(response.status_code, 200, url)
                        else:
                            self.assertEqual(response.status_code, 403, url)
                # Drop it from the Qualif
                q.helpers.remove(self.client.user)


class StateManagerUserTest(SeasonTestCaseMixin):
    def setUp(self):
        self.client = StateManagerAuthClient()
        super(StateManagerUserTest, self).setUp()

    def test_access_to_season_list(self):
        for symbolicurl in restrictedgenericurls:
            url = reverse(symbolicurl)
            # Final URL is forbidden
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)

    def test_access_to_season_detail(self):
        # The season is anything but archived
        for state in DV_SEASON_STATES:
            self.season.state = state[0]
            self.season.save()
            self.season.refresh_from_db()
            if state[0] != DV_SEASON_STATE_ARCHIVED:
                for symbolicurl in restrictedspecificurls:
                    url = reverse(symbolicurl, kwargs={"pk": self.season.pk})
                    # Final URL is OK
                    response = self.client.get(url, follow=True)
                    expected_status_code = 200
                    if (
                        symbolicurl == "season-set-running"
                        and not self.season.can_set_state_running
                    ):
                        # There are only some states in which we cna set the state to running
                        expected_status_code = 403
                    if (
                        symbolicurl == "season-set-open"
                        and not self.season.can_set_state_open
                    ):
                        # There are only some states in which we cna set the state to running
                        expected_status_code = 403
                    self.assertEqual(response.status_code, expected_status_code, url)

                for symbolicurl in restrictedhelperspecificurls:
                    for helper in self.users:
                        url = reverse(
                            symbolicurl,
                            kwargs={"pk": self.season.pk, "helperpk": helper.pk},
                        )
                        # Final URL is OK
                        response = self.client.get(url, follow=True)
                        self.assertEqual(response.status_code, 200, url)
                for exportformat in ["csv", "ods", "xls"]:
                    url = reverse(
                        "season-export",
                        kwargs={"pk": self.season.pk, "format": exportformat},
                    )
                    # Final URL is OK
                    response = self.client.get(url, follow=True)
                    self.assertEqual(response.status_code, 200, url)

    def test_season_runningplanning_accesses(self):
        # Loop over all states
        for state in DV_SEASON_STATES:
            self.season.state = state[0]
            self.season.save()
            url = reverse("season-set-running", kwargs={"pk": self.season.pk})
            response = self.client.get(url, follow=True)
            expected_status_code = 200
            if not self.season.can_set_state_running:
                expected_status_code = 403
            self.assertEqual(response.status_code, expected_status_code, url)

    def test_season_runningplanning(self):
        url = reverse("season-set-running", kwargs={"pk": self.season.pk})

        # Test that anything put that state works
        for state in DV_SEASON_STATES:
            # Set the season to be in preparation
            self.season.state = DV_SEASON_STATE_OPEN
            self.season.save()
            # Test that we can post to set it running
            response = self.client.post(url, {"state": state[0]})
            # 200 means that we're back on the page with an error
            expected_status_code = 200
            if state[0] == DV_SEASON_STATE_RUNNING:
                # 302 means that the post succeeded; so we can only post this state
                expected_status_code = 302
            self.assertEqual(response.status_code, expected_status_code, url)

    def test_season_openplanning_accesses(self):
        # Loop over all states
        for state in DV_SEASON_STATES:
            self.season.state = state[0]
            self.season.save()
            url = reverse("season-set-open", kwargs={"pk": self.season.pk})
            response = self.client.get(url, follow=True)
            expected_status_code = 200
            if not self.season.can_set_state_open:
                expected_status_code = 403
            self.assertEqual(response.status_code, expected_status_code, url)

    def test_season_openplanning(self):
        url = reverse("season-set-open", kwargs={"pk": self.season.pk})

        # Test that anything put that state works
        for state in DV_SEASON_STATES:
            # Set the season to be in preparation
            self.season.state = DV_SEASON_STATE_PLANNING
            self.season.save()
            # Test that we can post to set it running
            response = self.client.post(url, {"state": state[0]})
            # 200 means that we're back on the page with an error
            expected_status_code = 200
            if state[0] == DV_SEASON_STATE_OPEN:
                # 302 means that the post succeeded; so we can only post this state
                expected_status_code = 302
            self.assertEqual(response.status_code, expected_status_code, url)

    def test_season_creation(self):
        url = reverse("season-create")
        # Final URL is OK
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, url)

        initial = {
            "year": 2015,
            "month_start": 1,
            "n_months": 6,
            "cantons": [],
            "leader": self.client.user.pk,
            "state": DV_SEASON_STATE_OPEN,
        }

        # 200 because we're back on the page, because cantons' empty
        response = self.client.post(url, initial)
        self.assertEqual(response.status_code, 200, url)

        initial["cantons"] = self.foreigncantons
        # 200 because we're back on the page, because cantons' not our cantons
        response = self.client.post(url, initial)
        self.assertEqual(response.status_code, 200, url)

        initial["cantons"] = self.mycantons
        # That works now
        response = self.client.post(url, initial)
        self.assertEqual(response.status_code, 302, url)

    def test_session_creation(self):
        # The season is anything but archived
        for state in DV_SEASON_STATES:
            if state[0] != DV_SEASON_STATE_ARCHIVED:
                self.season.state = state[0]
                self.season.save()

                url = reverse("session-create", kwargs={"seasonpk": self.season.pk})
                # Final URL is OK
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)

                initial = {
                    "day": (self.season.begin).strftime(SWISS_DATE_INPUT_FORMAT),
                    "begin": "09:00",
                    "bikes_phone": "",
                }

                # 200 because we're back on the page, because orga' empty
                response = self.client.post(url, initial)
                self.assertEqual(response.status_code, 200, url)

                orga = OrganizationFactory(address_canton=self.foreignseason.cantons[0])
                initial["orga"] = orga.pk
                # 200 because we're back on the page, because orga is not
                # in our canton
                response = self.client.post(url, initial)
                self.assertEqual(response.status_code, 200, url)

                orga = OrganizationFactory(address_canton=self.season.cantons[0])
                initial["orga"] = orga.pk
                # That works now
                response = self.client.post(url, initial)
                self.assertEqual(response.status_code, 302, url)

    def test_user_can_edit_session(self):
        session = self.sessions[0]
        session.begin = datetime.time(9, 30)
        session.save()

        for state in DV_SEASON_STATES:
            if state[0] != DV_SEASON_STATE_ARCHIVED:
                self.season.state = state[0]
                self.season.save()
                self.client.post(
                    reverse(
                        "session-update",
                        kwargs={"pk": session.pk, "seasonpk": self.season.pk},
                    ),
                    data={
                        "orga": session.orga.pk,
                        "day": session.day,
                        "begin": "08:27",  # Modified !
                        "place": "",
                        "address_street": "",
                        "address_no": "",
                        "address_zip": "",
                        "address_city": "",
                        "address_canton": "",
                        "fallback_plan": "",
                        "superleader": "",
                        "bikes_concept": "",
                        "bikes_phone": "",
                        "apples": "",
                        "helpers_time": "07:30",
                        "helpers_place": "",
                        "comments": "",
                    },
                    follow=True,
                )

                session.refresh_from_db()
                self.assertEqual(session.begin, datetime.time(8, 27))

    def test_no_access_to_foreign_season(self):
        for symbolicurl in restrictedspecificurls:
            url = reverse(symbolicurl, kwargs={"pk": self.foreignseason.pk})
            # Final URL is NOK
            response = self.client.get(url, follow=True)
            # For helperlist and actorlist
            if symbolicurl in [
                "season-availabilities",
                "season-staff-update",
                "season-helperlist",
                "season-actorlist",
                "season-set-running",
                "season-set-open",
                "season-detail",
            ]:
                self.assertEqual(response.status_code, 403, url)
            else:
                self.assertEqual(response.status_code, 404, url)

    def test_no_access_to_foreignsession(self):
        for session in self.foreignsessions:
            urls = [
                reverse(
                    "session-list",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "year": session.day.year,
                        "week": session.day.strftime("%W"),
                    },
                ),
                reverse(
                    "session-create",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                    },
                ),
                reverse(
                    "session-detail",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-update",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-staff-choices",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-delete",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "pk": session.pk,
                    },
                ),
            ]
            for url in urls:
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 403, url)

    def test_access_to_mysession(self):
        # The season is anything but archived
        for state in DV_SEASON_STATES:
            if state[0] != DV_SEASON_STATE_ARCHIVED:
                self.season.state = state[0]
                self.season.save()
                for session in self.sessions:
                    urls = [
                        reverse(
                            "session-list",
                            kwargs={
                                "seasonpk": self.season.pk,
                                "year": session.day.year,
                                "week": session.day.strftime("%W"),
                            },
                        ),
                        reverse(
                            "session-create",
                            kwargs={
                                "seasonpk": self.season.pk,
                            },
                        ),
                        reverse(
                            "session-detail",
                            kwargs={
                                "seasonpk": self.season.pk,
                                "pk": session.pk,
                            },
                        ),
                        reverse(
                            "session-update",
                            kwargs={
                                "seasonpk": self.season.pk,
                                "pk": session.pk,
                            },
                        ),
                        reverse(
                            "session-staff-choices",
                            kwargs={
                                "seasonpk": self.season.pk,
                                "pk": session.pk,
                            },
                        ),
                        reverse(
                            "session-delete",
                            kwargs={
                                "seasonpk": self.season.pk,
                                "pk": session.pk,
                            },
                        ),
                    ]
                    for url in urls:
                        # Final URL is granted
                        response = self.client.get(url, follow=True)
                        self.assertEqual(response.status_code, 200, url)

    def test_access_to_my_archived_session(self):
        # The season is archived
        self.season.state = DV_SEASON_STATE_ARCHIVED
        self.season.save()
        for session in self.sessions:
            urls = [
                reverse(
                    "session-list",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "year": session.day.year,
                        "week": session.day.strftime("%W"),
                    },
                ),
                reverse(
                    "session-detail",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-staff-choices",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "pk": session.pk,
                    },
                ),
            ]
            for url in urls:
                # Final URL is granted
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)
        # Test the forbidden ones
        for session in self.sessions:
            urls = [
                reverse(
                    "session-create",
                    kwargs={
                        "seasonpk": self.season.pk,
                    },
                ),
                reverse(
                    "session-update",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-delete",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "pk": session.pk,
                    },
                ),
            ]
            for url in urls:
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 403, url)

    def test_access_to_quali_views(self):
        session = self.sessions[0]
        # Test the Qualification creation for a session
        url = reverse(
            "quali-create",
            kwargs={
                "seasonpk": session.season.pk,
                "sessionpk": session.pk,
            },
        )
        initial = {
            "session": session.pk,
            "name": "Classe A",
            "class_teacher_natel": "",
        }
        response = self.client.post(
            url,
            initial,
        )
        self.assertEqual(response.status_code, 302, url)

        qualification = session.qualifications.first()

        # Now test the Qualification update access for a session
        url = reverse(
            "quali-update",
            kwargs={
                "seasonpk": session.season.pk,
                "sessionpk": session.pk,
                "pk": qualification.pk,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)

        # Test Quali update now
        initial = {"session": qualification.session.pk, "name": "Classe D"}
        response = self.client.post(url, initial)
        self.assertEqual(response.status_code, 302, url)


class PowerUserTest(SeasonTestCaseMixin):
    def setUp(self):
        self.client = PowerUserAuthClient()
        super(PowerUserTest, self).setUp()

    def test_access_to_season_list(self):
        for symbolicurl in restrictedgenericurls:
            url = reverse(symbolicurl)
            # Final URL is forbidden
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)

    def test_access_to_season_detail(self):
        for symbolicurl in restrictedspecificurls:
            url = reverse(symbolicurl, kwargs={"pk": self.season.pk})
            # Final URL is OK
            response = self.client.get(url, follow=True)
            if "season-set-open" == symbolicurl and not self.season.can_set_state_open:
                self.assertEqual(response.status_code, 403, url)
            else:
                self.assertEqual(response.status_code, 200, url)
        for symbolicurl in restrictedhelperspecificurls:
            for helper in self.users:
                url = reverse(
                    symbolicurl, kwargs={"pk": self.season.pk, "helperpk": helper.pk}
                )
                # Final URL is OK
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)

    def test_access_to_foreignsession(self):
        for session in self.foreignsessions:
            urls = [
                reverse(
                    "session-list",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "year": session.day.year,
                        "week": session.day.strftime("%W"),
                    },
                ),
                reverse(
                    "session-create",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                    },
                ),
                reverse(
                    "session-detail",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-update",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-staff-choices",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-delete",
                    kwargs={
                        "seasonpk": self.foreignseason.pk,
                        "pk": session.pk,
                    },
                ),
            ]
            for url in urls:
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)

    def test_access_to_mysession(self):
        for session in self.sessions:
            urls = [
                reverse(
                    "session-list",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "year": session.day.year,
                        "week": session.day.strftime("%W"),
                    },
                ),
                reverse(
                    "session-create",
                    kwargs={
                        "seasonpk": self.season.pk,
                    },
                ),
                reverse(
                    "session-detail",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-update",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-staff-choices",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "pk": session.pk,
                    },
                ),
                reverse(
                    "session-delete",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "pk": session.pk,
                    },
                ),
            ]
            for url in urls:
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)


def test_session_to_season_all_months_in_year(db):
    # A year full of seasons
    [
        SeasonFactory(cantons=["VD"], year=2019, month_start=month_start, n_months=1)
        for month_start in range(1, 13)
    ]

    session = SessionFactory(
        day=datetime.date(2019, 4, 12),
        orga=OrganizationFactory(address_canton="VD"),
    )

    assert session.season.month_start == 4


def test_session_to_season_any_month_in_year(db):
    # A year full of 3 months seasons
    SeasonFactory(cantons=["VD"], year=2019, month_start=1, n_months=3)
    SeasonFactory(cantons=["VD"], year=2019, month_start=4, n_months=3)
    SeasonFactory(cantons=["VD"], year=2019, month_start=7, n_months=3)
    SeasonFactory(cantons=["VD"], year=2019, month_start=10, n_months=3)

    for month in range(1, 13):
        session = SessionFactory(
            day=datetime.date(2019, month, 12),
            orga=OrganizationFactory(address_canton="VD"),
        )

        assert session.season.begin <= session.day
        assert session.season.end >= session.day


def test_session_to_season_in_previous_year(db):
    # Seasons crossing the year boundary
    SeasonFactory(cantons=["VD"], year=2019, month_start=7, n_months=3)
    SeasonFactory(cantons=["VD"], year=2019, month_start=10, n_months=6)
    SeasonFactory(cantons=["VD"], year=2020, month_start=4, n_months=3)

    session = SessionFactory(
        day=datetime.date(2020, 2, 12),
        orga=OrganizationFactory(address_canton="VD"),
    )

    assert session.season.begin <= session.day
    assert session.season.end >= session.day


class CoordinatorUserTest(SeasonTestCaseMixin):
    def setUp(self):
        self.client = CoordinatorAuthClient()
        super().setUp()
        # Put the sessions for our Coordinator's orga
        for s in self.sessions:
            s.orga.coordinator = self.client.user
            s.orga.save()

    def test_cooordinator_can_navigate_sessions(self):
        # Test the access to the session on all season states
        for state in DV_SEASON_STATES:
            self.season.state = state[0]
            self.season.save()
            for session in self.sessions:
                urls = [
                    reverse(
                        "session-list",
                        kwargs={
                            "seasonpk": self.season.pk,
                            "year": session.day.year,
                            "week": session.day.strftime("%W"),
                        },
                    ),
                    reverse(
                        "session-detail",
                        kwargs={
                            "seasonpk": self.season.pk,
                            "pk": session.pk,
                        },
                    ),
                ]
                for url in urls:
                    # Coordinators can navigate the seasons in all states
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200, url)

    def test_coordinator_can_update_sessions(self):
        # Test the access to the session on all season states
        for state in DV_SEASON_STATES:
            self.season.state = state[0]
            self.season.save()
            for session in self.sessions:
                url = reverse(
                    "session-update",
                    kwargs={
                        "seasonpk": self.season.pk,
                        "pk": session.pk,
                    },
                )
                response = self.client.get(
                    url,
                    follow=True,
                )
                if state[0] in [DV_SEASON_STATE_PLANNING, DV_SEASON_STATE_OPEN]:
                    # Coordinator can update sessions only in planning
                    self.assertEqual(response.status_code, 200, url)
                else:
                    self.assertEqual(response.status_code, 403, url)

    def test_coordinator_cannot_create_nor_delete_sessions(self):
        # Test the access to the session on all season states
        for state in DV_SEASON_STATES:
            self.season.state = state[0]
            self.season.save()
            for session in self.sessions:
                urls = [
                    reverse(
                        "session-create",
                        kwargs={
                            "seasonpk": self.season.pk,
                        },
                    ),
                    reverse(
                        "session-delete",
                        kwargs={
                            "seasonpk": self.season.pk,
                            "pk": session.pk,
                        },
                    ),
                ]
                for url in urls:
                    # Final URL is forbidden; no creation nor deletion by coordinators
                    response = self.client.get(url, follow=True)
                    self.assertEqual(response.status_code, 403, url)
