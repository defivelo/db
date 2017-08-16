# -*- coding: utf-8 -*-
#
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
from __future__ import unicode_literals

import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.urlresolvers import NoReverseMatch, reverse
from django.test import TestCase

from apps.common import DV_STATES
from apps.user.models import (
    BAGSTATUS_LOAN, BAGSTATUS_PAID, FORMATION_M1, FORMATION_M2, STD_PROFILE_FIELDS, USERSTATUS_ACTIVE,
    USERSTATUS_INACTIVE,
)
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import AuthClient, PowerUserAuthClient, StateManagerAuthClient, SuperUserAuthClient

myurlsforall = ['user-detail', 'user-update', 'profile-detail', ]
myurlsforoffice = ['user-list', 'user-list-export', ]

othersurls = ['user-detail', 'user-update', 'user-create',
              'user-sendcredentials', ]

superadminurls = ['user-resendcredentials', ]

profile_autocompletes = ['Actors', 'AllPersons', 'Leaders', 'Helpers',
                         'PersonsRelevantForSessions']


def tryurl(symbolicurl, user, exportformat='csv'):
    try:
        try:
            url = reverse(
                symbolicurl, kwargs={'pk': user.pk}
                )
        except NoReverseMatch:
            url = reverse(
                symbolicurl, kwargs={'format': exportformat}
                )
    except NoReverseMatch:
        url = reverse(symbolicurl)
    return url


class ProfileTestCase(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = AuthClient()
        self.users = [UserFactory() for i in range(3)]

    def getprofileinitial(self, user):
        userfields = ['first_name', 'last_name', 'email']

        initial = {
            k: v for (k, v)
            in user.__dict__.items()
            if k in userfields
            }
        initial.update(
            {
                k: v for (k, v)
                in user.profile.__dict__.items()
                if k in STD_PROFILE_FIELDS
                })

        # Some corrections
        initial['status'] = 0
        initial['birthdate'] = ''
        initial['formation_lastdate'] = ''

        if not initial['activity_cantons']:
            initial['activity_cantons'] = []

        return initial


class AuthUserTest(ProfileTestCase):
    def test_my_allowances(self):
        for symbolicurl in myurlsforall:
            url = tryurl(symbolicurl, self.client.user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_my_restrictions(self):
        for symbolicurl in myurlsforoffice:
            for exportformat in ['csv', 'ods', 'xls']:
                url = tryurl(symbolicurl, self.client.user, exportformat)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403, url)

    def test_otherusers_access(self):
        for symbolicurl in othersurls:
            for otheruser in self.users:
                url = tryurl(symbolicurl, otheruser)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403, url)

    def test_my_profile_access(self):
        # Pre-update profile and user
        self.client.user.profile.formation = FORMATION_M1
        self.client.user.profile.affiliation_canton = 'GE'
        self.client.user.profile.bagstatus = BAGSTATUS_LOAN
        self.client.user.profile.status = USERSTATUS_ACTIVE
        self.client.user.profile.save()
        url = reverse('user-update',
                      kwargs={'pk': self.client.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)

        initial = self.getprofileinitial(self.client.user)
        # Test some update, that must go through
        initial['first_name'] = 'newfirstname'
        initial['activity_cantons'] = ['JU', 'GE', 'VD', ]
        initial['status'] = USERSTATUS_INACTIVE

        # And some that mustn't
        initial['formation'] = FORMATION_M2
        initial['affiliation_canton'] = 'VD'
        initial['bagstatus'] = BAGSTATUS_PAID

        response = self.client.post(url, initial)
        self.assertEqual(response.status_code, 302, url)

        # Get our user from DB
        me = get_user_model().objects.get(pk=self.client.user.pk)

        # Updated
        self.assertEqual(me.first_name, 'newfirstname')
        self.assertEqual(me.profile.activity_cantons, ['JU', 'VD', ])
        self.assertEqual(me.profile.status, USERSTATUS_INACTIVE)

        # Not updated
        self.assertEqual(me.profile.formation, FORMATION_M1)
        self.assertEqual(me.profile.bagstatus, BAGSTATUS_LOAN)
        self.assertEqual(me.profile.affiliation_canton, 'GE')

    def test_autocompletes(self):
        # All autocompletes are forbidden
        for al in profile_autocompletes:
            url = reverse('user-%s-ac' % al)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)


class PowerUserTest(ProfileTestCase):
    def setUp(self):
        super(PowerUserTest, self).setUp()
        self.client = PowerUserAuthClient()

    def test_my_allowances(self):
        for symbolicurl in myurlsforall + myurlsforoffice:
            for exportformat in ['csv', 'ods', 'xls']:
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
            url = tryurl('user-sendcredentials', otheruser)
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

            # Second try should fail, now that each of the users has a
            # a valid email and got a password sent
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)

            # Allowed to re-send creds though, any number of times
            for i in range(2):
                url = tryurl('user-resendcredentials', otheruser)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

                response = self.client.post(url, {})
                self.assertEqual(response.status_code, 302, url)

                nmails += 1
                self.assertEqual(len(mail.outbox), nmails)

    def test_other_profile_accesses(self):
        for user in self.users:
            # Pre-update profile and user
            user.profile.formation = FORMATION_M1
            user.profile.save()
            url = reverse('user-update', kwargs={'pk': user.pk})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

            initial = self.getprofileinitial(user)
            # Test some update, that must go through
            initial['first_name'] = 'newfirstname'
            initial['activity_cantons'] = ['JU', 'VD', 'GE', ]

            # And some that mustn't
            initial['formation'] = FORMATION_M2
            initial['affiliation_canton'] = 'VD'

            response = self.client.post(url, initial)
            self.assertEqual(response.status_code, 302, url)

            # Get our user from DB
            her = get_user_model().objects.get(pk=user.pk)

            # Updated
            self.assertEqual(her.first_name, 'newfirstname')
            # Pas de VD parce que le canton d'affiliation est 'VD'
            self.assertEqual(her.profile.activity_cantons, ['JU', 'GE', ])

            # Updated as well
            self.assertEqual(her.profile.formation, FORMATION_M2)
            self.assertEqual(her.profile.affiliation_canton, 'VD')

    def test_autocompletes(self):
        # All autocompletes are permitted
        for al in profile_autocompletes:
            url = reverse('user-%s-ac' % al)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)


class StateManagerUserTest(ProfileTestCase):
    def setUp(self):
        super(StateManagerUserTest, self).setUp()
        self.client = StateManagerAuthClient()
        mycanton = str((self.client.user.managedstates.first()).canton)

        OTHERSTATES = [c for c in DV_STATES if c != mycanton]
        for user in self.users:
            user.profile.affiliation_canton = OTHERSTATES[0]
            user.profile.save()

        self.users[0].profile.affiliation_canton = mycanton
        self.users[0].profile.save()

        self.myuser = self.users[0]
        self.foreignuser = self.users[1]

    def test_my_allowances(self):
        for symbolicurl in myurlsforall + myurlsforoffice:
            for exportformat in ['csv', 'ods', 'xls']:
                url = tryurl(symbolicurl, self.client.user, exportformat)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

    def test_otherusers_access(self):
        response = self.client.get(reverse('user-detail',
                                   kwargs={'pk': self.myuser.pk}))
        self.assertTemplateUsed(response, 'auth/user_detail.html')
        self.assertEqual(response.status_code, 200, response)

        # The other user cannot be accessed
        response = self.client.get(reverse('user-detail',
                                   kwargs={'pk': self.foreignuser.pk}))
        self.assertEqual(response.status_code, 403)

    def test_otherusers_edit(self):
        url = reverse('user-update', kwargs={'pk': self.myuser.pk})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'auth/user_form.html')
        self.assertEqual(response.status_code, 200, response)

        # Our orga cannot be edited away from my cantons
        initial = self.getprofileinitial(self.myuser)
        initial['address_no'] = 24

        response = self.client.post(url, initial)
        # Code 302 because update succeeded
        self.assertEqual(response.status_code, 302, url)
        # Check update succeeded
        newuser = get_user_model().objects.get(pk=self.myuser.pk)
        self.assertEqual(newuser.profile.address_no, '24')

        # Test some update, that must go through
        initial['affiliation_canton'] = \
            self.foreignuser.profile.affiliation_canton

        response = self.client.post(url, initial)
        # Code 200 because update failed
        self.assertEqual(response.status_code, 200, url)
        # Check update failed
        newuser = get_user_model().objects.get(pk=self.myuser.pk)
        self.assertEqual(
            newuser.profile.affiliation_canton,
            self.myuser.profile.affiliation_canton
        )

        # The other user cannot be accessed
        response = self.client.get(reverse('user-update',
                                   kwargs={'pk': self.foreignuser.pk}))
        self.assertEqual(response.status_code, 403)

    def test_autocompletes(self):
        for al in ['AllPersons']:
            url = reverse('user-%s-ac' % al)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            # Check that we only find ourselves
            entries = re.findall('"id": "(\d+)"', str(response.content))
            self.assertEqual(entries, [str(self.myuser.pk)])


class SuperUserTest(ProfileTestCase):
    def setUp(self):
        super(SuperUserTest, self).setUp()
        self.client = SuperUserAuthClient()

    def test_send_creds(self):
        nmails = 0
        for otheruser in self.users:
            url = tryurl('user-sendcredentials', otheruser)
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

            # Second try should fail, now that each of the users has a
            # a valid email and got a password sent
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)

            # Allowed to re-send creds though, any number of times
            for i in range(2):
                url = tryurl('user-resendcredentials', otheruser)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

                response = self.client.post(url, {})
                self.assertEqual(response.status_code, 302, url)

                nmails += 1
                self.assertEqual(len(mail.outbox), nmails)
