# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016 Didier Raboud <me+defivelo@odyx.org>
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

from django.core.urlresolvers import reverse
from django.test import TestCase

from apps.common import DV_STATES
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import (
    AuthClient, PowerUserAuthClient, StateManagerAuthClient,
)

from .factories import SeasonFactory, SessionFactory

restrictedgenericurls = ['season-list', 'season-create']
restrictedspecificurls = ['season-detail', 'season-update',
                          'season-helperlist', 'season-actorlist',
                          'season-availabilities',
                          'season-staff-update',
                          'season-delete',
                          ]
restrictedhelperspecificurls = ['season-availabilities-update', ]


class SeasonTestCaseMixin(TestCase):
    def setUp(self):
        self.users = [UserFactory() for i in range(3)]

        self.season = SeasonFactory()
        mycantons = [c.canton for c in self.client.user.managedstates.all()]
        if mycantons:
            self.season.cantons = mycantons
        else:
            self.season.cantons = [DV_STATES[0], ]
        self.season.save()

        self.sessions = []
        for canton in mycantons:
            s = SessionFactory()
            s.organization.address_canton = canton
            s.organization.save()
            s.save()
            self.sessions.append(s)

        OTHERSTATES = [c for c in DV_STATES if c not in mycantons]
        self.foreignseason = SeasonFactory(cantons=OTHERSTATES)
        self.foreignseason.save()

        self.foreignsessions = []
        for canton in OTHERSTATES:
            s = SessionFactory()
            s.organization.address_canton = canton
            s.organization.save()
            s.save()
            self.foreignsessions.append(s)


class AuthUserTest(SeasonTestCaseMixin):
    def setUp(self):
        self.client = AuthClient()
        super(AuthUserTest, self).setUp()

    def test_no_access_to_season_list(self):
        for symbolicurl in restrictedgenericurls:
            url = reverse(symbolicurl)
            # Final URL is forbidden
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 403, url)

    def test_no_access_to_season_detail(self):
        for symbolicurl in restrictedspecificurls:
            url = reverse(symbolicurl, kwargs={'pk': self.season.pk})
            # Final URL is forbidden
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 403, url)
        for symbolicurl in restrictedhelperspecificurls:
            for helper in self.users:
                url = reverse(
                    symbolicurl,
                    kwargs={
                        'pk': self.season.pk,
                        'helperpk': helper.pk
                        })
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 403, url)

    def test_no_access_to_session(self):
        for session in self.sessions:
            urls = [
                reverse(
                    'session-list',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'year': session.day.year,
                        'week': session.day.strftime('%W'),
                    }),
                reverse(
                    'session-create',
                    kwargs={
                        'seasonpk': self.season.pk,
                    }),
                reverse(
                    'session-detail',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-update',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-staff-choices',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-delete',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
            ]
            for url in urls:
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 403, url)


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
        for symbolicurl in restrictedspecificurls:
            url = reverse(symbolicurl, kwargs={'pk': self.season.pk})
            # Final URL is OK
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)
        for symbolicurl in restrictedhelperspecificurls:
            for helper in self.users:
                url = reverse(
                    symbolicurl,
                    kwargs={
                        'pk': self.season.pk,
                        'helperpk': helper.pk
                        })
                # Final URL is OK
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)

    def test_access_to_foreign_season(self):
        for symbolicurl in restrictedspecificurls:
            url = reverse(symbolicurl, kwargs={'pk': self.foreignseason.pk})
            # Final URL is NOK
            response = self.client.get(url, follow=True)
            # For helperlist and actorlist
            if 'list' in symbolicurl:
                self.assertEqual(response.status_code, 403, url)
            else:
                self.assertEqual(response.status_code, 404, url)

    def test_no_access_to_foreignsession(self):
        for session in self.foreignsessions:
            urls = [
                reverse(
                    'session-list',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'year': session.day.year,
                        'week': session.day.strftime('%W'),
                    }),
                reverse(
                    'session-create',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                    }),
                reverse(
                    'session-detail',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-update',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-staff-choices',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-delete',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'pk': session.pk,
                    }),
            ]
            for url in urls:
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 403, url)

    def test_access_to_mysession(self):
        for session in self.sessions:
            urls = [
                reverse(
                    'session-list',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'year': session.day.year,
                        'week': session.day.strftime('%W'),
                    }),
                reverse(
                    'session-create',
                    kwargs={
                        'seasonpk': self.season.pk,
                    }),
                reverse(
                    'session-detail',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-update',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-staff-choices',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-delete',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
            ]
            for url in urls:
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)


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
            url = reverse(symbolicurl, kwargs={'pk': self.season.pk})
            # Final URL is OK
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)
        for symbolicurl in restrictedhelperspecificurls:
            for helper in self.users:
                url = reverse(
                    symbolicurl,
                    kwargs={
                        'pk': self.season.pk,
                        'helperpk': helper.pk
                        })
                # Final URL is OK
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)

    def test_access_to_foreignsession(self):
        for session in self.foreignsessions:
            urls = [
                reverse(
                    'session-list',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'year': session.day.year,
                        'week': session.day.strftime('%W'),
                    }),
                reverse(
                    'session-create',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                    }),
                reverse(
                    'session-detail',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-update',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-staff-choices',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-delete',
                    kwargs={
                        'seasonpk': self.foreignseason.pk,
                        'pk': session.pk,
                    }),
            ]
            for url in urls:
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)

    def test_access_to_mysession(self):
        for session in self.sessions:
            urls = [
                reverse(
                    'session-list',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'year': session.day.year,
                        'week': session.day.strftime('%W'),
                    }),
                reverse(
                    'session-create',
                    kwargs={
                        'seasonpk': self.season.pk,
                    }),
                reverse(
                    'session-detail',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-update',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-staff-choices',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
                reverse(
                    'session-delete',
                    kwargs={
                        'seasonpk': self.season.pk,
                        'pk': session.pk,
                    }),
            ]
            for url in urls:
                # Final URL is forbidden
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200, url)
