# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015 Didier Raboud <me+defivelo@odyx.org>
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

import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from rolepermissions.roles import get_user_roles

from apps.common import DV_STATES
from apps.user import FORMATION_M1, FORMATION_M2
from apps.user.models import (
    BAGSTATUS_LOAN,
    BAGSTATUS_NONE,
    BAGSTATUS_PAID,
    STD_PROFILE_FIELDS,
    USERSTATUS_ACTIVE,
    USERSTATUS_INACTIVE,
)
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import (
    AuthClient,
    CollaboratorAuthClient,
    CoordinatorAuthClient,
    PowerUserAuthClient,
    StateManagerAuthClient,
    SuperUserAuthClient,
)

User = get_user_model()

myurlsforall = [
    "user-detail",
    "user-update",
    "profile-detail",
]
myurls_for_office_and_collaborators = [
    "user-list",
    "user-list-export",
]

othersurls = [
    "user-detail",
    "user-update",
    "user-create",
    "user-sendcredentials",
    "user-delete",
]

profile_autocompletes = [
    "Actors",
    "AllPersons",
    "Leaders",
    "Helpers",
    "PersonsRelevantForSessions",
]


def tryurl(symbolicurl, user, exportformat="csv"):
    try:
        try:
            url = reverse(symbolicurl, kwargs={"pk": user.pk})
        except NoReverseMatch:
            url = reverse(symbolicurl, kwargs={"format": exportformat})
    except NoReverseMatch:
        url = reverse(symbolicurl)
    return url


class ProfileTestCase(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = AuthClient()
        self.users = [UserFactory(profile__affiliation_canton="NE") for i in range(3)]

    def getprofileinitial(self, user):
        userfields = ["first_name", "last_name", "email"]

        initial = {k: v for (k, v) in user.__dict__.items() if k in userfields}
        initial.update(
            {
                k: v
                for (k, v) in user.profile.__dict__.items()
                if k in STD_PROFILE_FIELDS
            }
        )

        # Some corrections
        initial["language"] = "fr"
        initial["status"] = 0
        initial["birthdate"] = ""
        initial["formation_firstdate"] = ""
        initial["formation_lastdate"] = ""

        if not initial["activity_cantons"]:
            initial["activity_cantons"] = []

        if not initial["languages_challenges"]:
            initial["languages_challenges"] = []

        return initial


class AuthUserTest(ProfileTestCase):
    def test_my_allowances(self):
        for symbolicurl in myurlsforall:
            url = tryurl(symbolicurl, self.client.user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_my_restrictions(self):
        for symbolicurl in myurls_for_office_and_collaborators + [
            "user-assign-role",
        ]:
            for exportformat in ["csv", "ods", "xls"]:
                url = tryurl(symbolicurl, self.client.user, exportformat)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403, url)

    def test_otherusers_access(self):
        for symbolicurl in othersurls + [
            "user-assign-role",
        ]:
            for otheruser in self.users:
                url = tryurl(symbolicurl, otheruser)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403, url)

    def test_my_profile_access(self):
        # Pre-update profile and user
        self.client.user.profile.formation = FORMATION_M1
        self.client.user.profile.affiliation_canton = "GE"
        self.client.user.profile.bagstatus = BAGSTATUS_LOAN
        self.client.user.profile.status = USERSTATUS_ACTIVE
        self.client.user.profile.language = "fr"
        self.client.user.profile.cresus_employee_number = "poor"
        self.client.user.profile.save()
        url = reverse("user-update", kwargs={"pk": self.client.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)

        initial = self.getprofileinitial(self.client.user)
        # Test some update, that must go through
        initial["first_name"] = "newfirstname"
        initial["activity_cantons"] = [
            "JU",
            "GE",
            "VD",
        ]
        initial["language"] = "de"
        initial["languages_challenges"] = [
            "de",
            "fr",
        ]
        initial["status"] = USERSTATUS_INACTIVE
        initial["bank_name"] = "Banque Alternative Suisse, succursale de Lausanne"

        # And some that mustn't
        initial["formation"] = FORMATION_M2
        initial["affiliation_canton"] = "VD"
        initial["bagstatus"] = BAGSTATUS_PAID
        initial["cresus_employee_number"] = "I want to be rich"

        response = self.client.post(url, initial)
        self.assertEqual(response.status_code, 302, url)

        # Get our user from DB
        me = get_user_model().objects.get(pk=self.client.user.pk)

        # Updated
        self.assertEqual(me.first_name, "newfirstname")
        self.assertEqual(
            me.profile.activity_cantons,
            [
                "JU",
                "VD",
            ],
        )
        self.assertEqual(me.profile.language, "de")
        self.assertEqual(
            me.profile.languages_challenges,
            [
                "fr",
            ],
        )
        self.assertEqual(me.profile.status, USERSTATUS_INACTIVE)
        self.assertEqual(
            me.profile.bank_name, "Banque Alternative Suisse, succursale de Lausanne"
        )

        # Not updated
        self.assertEqual(me.profile.cresus_employee_number, "poor")
        self.assertEqual(me.profile.formation, FORMATION_M1)
        self.assertEqual(me.profile.bagstatus, BAGSTATUS_LOAN)
        self.assertEqual(me.profile.affiliation_canton, "GE")

    def test_autocompletes(self):
        # All autocompletes are forbidden
        for al in profile_autocompletes:
            url = "%s?q=test" % reverse("user-%s-ac" % al)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)


class CollaboratorUserTest(AuthUserTest):
    def setUp(self):
        super().setUp()
        self.client = CollaboratorAuthClient()

    def test_my_allowances(self):
        for symbolicurl in myurlsforall + myurls_for_office_and_collaborators:
            for exportformat in ["csv", "ods", "xls"]:
                url = tryurl(symbolicurl, self.client.user, exportformat)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

    def test_my_restrictions(self):
        # Collaborators can't assign roles.
        url = tryurl(
            "user-assign-role",
            self.client.user,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, url)

    def test_autocompletes(self):
        # Autocompletes are OK for collaborators, they have access to the user list.
        for al in profile_autocompletes:
            url = "%s?q=test" % reverse("user-%s-ac" % al)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)


class PowerUserTest(ProfileTestCase):
    def setUp(self):
        super(PowerUserTest, self).setUp()
        self.client = PowerUserAuthClient()

    def test_my_allowances(self):
        for symbolicurl in myurlsforall + myurls_for_office_and_collaborators:
            for exportformat in ["csv", "ods", "xls"]:
                url = tryurl(symbolicurl, self.client.user, exportformat)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

    def test_otherusers_access(self):
        for symbolicurl in othersurls:
            for otheruser in self.users:
                url = tryurl(symbolicurl, otheruser)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

    def test_send_creds(self):
        nmails = 0
        for otheruser in self.users:
            url = tryurl("user-sendcredentials", otheruser)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            # Now post to it, to get the mail sent
            response = self.client.post(url, {})
            self.assertEqual(response.status_code, 302, url)

            nmails += 1
            self.assertEqual(len(mail.outbox), nmails)

            # Verify what they are from the DB
            dbuser = get_user_model().objects.get(pk=otheruser.pk)
            self.assertTrue(dbuser.is_active)
            self.assertTrue(dbuser.has_usable_password())
            self.assertTrue(dbuser.profile.can_login)
            self.assertFalse(dbuser.profile.deleted)

            # Second try should fail, now that each of the users has a
            # a valid email and got a password sent
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)

            # Allowed to re-send creds though, any number of times
            for i in range(2):
                url = tryurl("user-resendcredentials", otheruser)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

                response = self.client.post(url, {})
                self.assertEqual(response.status_code, 302, url)

                nmails += 1
                self.assertEqual(len(mail.outbox), nmails)

            url = tryurl("user-delete", otheruser)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            # Now post to it, to remove the user
            response = self.client.post(url, {})
            self.assertEqual(response.status_code, 302, url)
            # Get again
            dbuser = get_user_model().objects.get(pk=otheruser.pk)

            self.assertFalse(dbuser.profile.can_login)
            self.assertTrue(dbuser.profile.deleted)

    def test_other_profile_accesses(self):
        for user in self.users:
            # Pre-update profile and user
            user.profile.formation = FORMATION_M1
            user.profile.cresus_employee_number = "rich"
            user.profile.save()
            url = reverse("user-update", kwargs={"pk": user.pk})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

            initial = self.getprofileinitial(user)
            # Test some update, that must go through
            initial["first_name"] = "newfirstname"
            initial["activity_cantons"] = [
                "JU",
                "VD",
                "GE",
            ]
            initial["cresus_employee_number"] = "poor"
            initial["formation"] = FORMATION_M2
            initial["affiliation_canton"] = "VD"

            response = self.client.post(url, initial)
            self.assertEqual(response.status_code, 302, url)

            # Get our user from DB
            her = get_user_model().objects.get(pk=user.pk)

            # Updated
            self.assertEqual(her.first_name, "newfirstname")
            # Pas de VD parce que le canton d'affiliation est 'VD'
            self.assertEqual(
                her.profile.activity_cantons,
                [
                    "JU",
                    "GE",
                ],
            )

            # Updated as well
            self.assertEqual(her.profile.formation, FORMATION_M2)
            self.assertEqual(her.profile.affiliation_canton, "VD")
            self.assertEqual(her.profile.cresus_employee_number, "poor")

    def test_roleassign(self):
        # Can't change my own role
        url = reverse("user-assign-role", kwargs={"pk": self.client.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, response)

        # But I can change any other role
        user = self.users[0]
        # Make this user a without-role user
        user.profile.formation = ""
        user.profile.actor_for.clear()
        user.profile.save()

        url = reverse("user-assign-role", kwargs={"pk": user.pk})
        response = self.client.get(url)
        # That user has no login
        self.assertEqual(response.status_code, 403, response)

        url = tryurl("user-sendcredentials", user)
        # Now post to it, to get the mail sent
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302, url)

        url = reverse("user-assign-role", kwargs={"pk": user.pk})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "roles/assign.html")
        self.assertEqual(response.status_code, 200, response)
        self.assertEqual(get_user_roles(user), [], user)
        response = self.client.post(
            url,
            {
                "role": "state_manager",
                "managed_states": [
                    "VD",
                ],
            },
        )
        self.assertEqual(response.status_code, 302, url)
        self.assertEqual(
            list(user.managedstates.all().values_list("canton", flat=True)),
            ["VD"],
            user,
        )
        self.assertEqual(
            [r.get_name() for r in get_user_roles(user)], ["state_manager"], user
        )

        response = self.client.post(
            url,
            {
                "role": "power_user",
                "managed_states": [
                    "VD",
                ],
            },
        )
        self.assertEqual(response.status_code, 302, url)
        # No canton for non-state_manager
        self.assertEqual(
            list(user.managedstates.all().values_list("canton", flat=True)), [], user
        )
        self.assertEqual(
            [r.get_name() for r in get_user_roles(user)], ["power_user"], user
        )

        # Deleting the role also works
        response = self.client.post(url, {"role": "", "managed_states": ["VD"]})
        self.assertEqual(response.status_code, 302, url)
        self.assertEqual(get_user_roles(user), [], user)
        # No canton for non-state_manager
        self.assertEqual(
            list(user.managedstates.all().values_list("canton", flat=True)), [], user
        )

    def test_autocompletes(self):
        # All autocompletes are permitted
        for al in profile_autocompletes:
            url = "%s?q=test" % reverse("user-%s-ac" % al)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)


class CoordinatorUserTest(ProfileTestCase):
    def setUp(self):
        super().setUp()
        self.client = CoordinatorAuthClient()
        for user in self.users:
            user.profile.save()

    def test_my_allowances(self):
        for symbolicurl in myurlsforall:
            for exportformat in ["csv", "ods", "xls"]:
                url = tryurl(symbolicurl, self.client.user, exportformat)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

    def test_my_profile_access(self):
        # Pre-update profile and user
        self.client.user.profile.formation = FORMATION_M1
        self.client.user.profile.affiliation_canton = "GE"
        self.client.user.profile.bagstatus = BAGSTATUS_LOAN
        self.client.user.profile.status = USERSTATUS_ACTIVE
        self.client.user.profile.language = "fr"
        self.client.user.profile.cresus_employee_number = "poor"
        self.client.user.profile.save()
        url = reverse("user-update", kwargs={"pk": self.client.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)

        initial = self.getprofileinitial(self.client.user)
        # Test some update, that must go through
        initial["first_name"] = "newfirstname"
        initial["activity_cantons"] = [
            "JU",
            "GE",
            "VD",
        ]
        initial["language"] = "de"
        initial["languages_challenges"] = [
            "de",
            "fr",
        ]
        initial["status"] = USERSTATUS_INACTIVE
        initial["bank_name"] = "Banque Alternative Suisse, succursale de Lausanne"

        # And some that mustn't
        initial["formation"] = FORMATION_M2
        initial["affiliation_canton"] = "VD"
        initial["bagstatus"] = BAGSTATUS_PAID
        initial["cresus_employee_number"] = "I want to be rich"

        response = self.client.post(url, initial)
        self.assertEqual(response.status_code, 302, url)

        # Get our user from DB
        me = get_user_model().objects.get(pk=self.client.user.pk)

        # Updated
        self.assertEqual(me.first_name, "newfirstname")
        self.assertEqual(
            me.profile.activity_cantons,
            [
                "JU",
                "VD",
            ],
        )
        self.assertEqual(me.profile.language, "de")
        self.assertEqual(
            me.profile.languages_challenges,
            [
                "fr",
            ],
        )
        self.assertEqual(me.profile.status, USERSTATUS_INACTIVE)
        self.assertEqual(
            me.profile.bank_name, "Banque Alternative Suisse, succursale de Lausanne"
        )

        # Not updated
        self.assertEqual(me.profile.cresus_employee_number, "poor")
        self.assertEqual(me.profile.formation, FORMATION_M1)
        self.assertEqual(me.profile.bagstatus, BAGSTATUS_LOAN)
        self.assertEqual(me.profile.affiliation_canton, "GE")

    def test_my_simple_profile_access(self):
        # Pre-update profile and user
        self.client.user.profile.status = USERSTATUS_ACTIVE
        self.client.user.profile.language = "fr"
        self.client.user.profile.save()
        url = reverse("user-update", kwargs={"pk": self.client.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)

        initial = self.getprofileinitial(self.client.user)
        # Test some update, that must go through
        initial["first_name"] = "newfirstname"
        initial["activity_cantons"] = [
            "JU",
            "GE",
            "VD",
        ]
        initial["language"] = "de"
        initial["languages_challenges"] = [
            "de",
            "fr",
        ]
        initial["status"] = USERSTATUS_INACTIVE
        initial["bank_name"] = "Banque Alternative Suisse, succursale de Lausanne"

        # And some that mustn't
        initial["formation"] = FORMATION_M2
        initial["affiliation_canton"] = "VD"
        initial["bagstatus"] = BAGSTATUS_PAID
        initial["cresus_employee_number"] = "I want to be rich"

        response = self.client.post(url, initial)
        self.assertEqual(response.status_code, 302, url)

        # Get our user from DB
        me = get_user_model().objects.get(pk=self.client.user.pk)

        # Updated
        self.assertEqual(me.first_name, "newfirstname")
        self.assertEqual(me.profile.language, "de")

        # Not updated
        self.assertEqual(me.profile.bank_name, "")
        self.assertEqual(me.profile.languages_challenges, [])
        self.assertEqual(me.profile.activity_cantons, [])
        self.assertEqual(me.profile.cresus_employee_number, "")
        self.assertEqual(me.profile.status, USERSTATUS_ACTIVE)
        self.assertEqual(me.profile.formation, "")
        self.assertEqual(me.profile.bagstatus, BAGSTATUS_NONE)
        self.assertEqual(me.profile.affiliation_canton, "")


class StateManagerUserTest(ProfileTestCase):
    def setUp(self):
        super(StateManagerUserTest, self).setUp()
        self.client = StateManagerAuthClient()
        mycanton = str((self.client.user.managedstates.first()).canton)

        OTHERSTATES = [c for c in DV_STATES if c != mycanton]
        for user in self.users:
            user.profile.affiliation_canton = OTHERSTATES[0]
            user.profile.cresus_employee_number = "poor"
            user.profile.save()

        self.users[0].profile.affiliation_canton = mycanton
        self.users[0].profile.save()

        self.myuser = self.users[0]
        self.foreignuser = self.users[1]

    def test_accented_search(self):
        self.users[0].first_name = "Joël"
        self.users[0].save()
        response = self.client.get("%s?%s" % (reverse("user-list"), "q=joel"))
        self.assertContains(response, "Joël")

    def test_my_allowances(self):
        for symbolicurl in myurlsforall + myurls_for_office_and_collaborators:
            for exportformat in ["csv", "ods", "xls"]:
                url = tryurl(symbolicurl, self.client.user, exportformat)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

    def test_otherusers_access(self):
        response = self.client.get(
            reverse("user-detail", kwargs={"pk": self.myuser.pk})
        )
        self.assertTemplateUsed(response, "auth/user_detail.html")
        self.assertEqual(response.status_code, 200, response)

        # The other user can also be accessed
        response = self.client.get(
            reverse("user-detail", kwargs={"pk": self.foreignuser.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_otherusers_edit(self):
        url = reverse("user-update", kwargs={"pk": self.myuser.pk})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "auth/user_form.html")
        self.assertEqual(response.status_code, 200, response)

        # Our orga cannot be edited away from my cantons
        initial = self.getprofileinitial(self.myuser)
        initial["address_no"] = 24

        response = self.client.post(url, initial)
        # Code 302 because update succeeded
        self.assertEqual(response.status_code, 302, url)
        # Check update succeeded
        newuser = get_user_model().objects.get(pk=self.myuser.pk)
        self.assertEqual(newuser.profile.address_no, "24")

        # Test modifying the affiliation canton _away_
        initial["affiliation_canton"] = self.foreignuser.profile.affiliation_canton
        # And modifying settings only accessible to Bureau
        initial["cresus_employee_number"] = "rich"
        initial["comments"] = "Nasty comment"

        response = self.client.post(url, initial)
        # Code 200 because update failed
        self.assertEqual(response.status_code, 200, url)
        # Check update failed
        newuser = get_user_model().objects.get(pk=self.myuser.pk)
        self.assertEqual(
            newuser.profile.affiliation_canton, self.myuser.profile.affiliation_canton
        )
        self.assertEqual(newuser.profile.cresus_employee_number, "poor")
        self.assertEqual(newuser.profile.comments, "")

        # The other user cannot be accessed
        response = self.client.get(
            reverse("user-update", kwargs={"pk": self.foreignuser.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_cannot_update_cresus_number(self):
        url = reverse("user-update", kwargs={"pk": self.myuser.pk})
        initial = self.getprofileinitial(self.myuser)
        initial["cresus_employee_number"] = "rich"

        self.client.post(url, initial)

        self.myuser.profile.refresh_from_db()
        self.assertEqual(self.myuser.profile.cresus_employee_number, "poor")

    def test_autocompletes(self):
        for al in ["AllPersons"]:
            url = reverse("user-%s-ac" % al)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            # Check that we find everyone, including users of other cantons
            entries = re.findall(r'"id": "(\d+)"', str(response.content))
            expected_entries = set(str(u.id) for u in User.objects.all())
            self.assertEqual(set(entries), expected_entries)


class SuperUserTest(ProfileTestCase):
    def setUp(self):
        super(SuperUserTest, self).setUp()
        self.client = SuperUserAuthClient()
