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

from defivelo.tests.utils import AuthClient, PowerUserAuthClient

from .factories import SeasonFactory

restrictedgenericurls = ['season-list', 'season-create']
restrictedspecificurls = ['season-detail', 'season-update',
                          'season-helperlist', 'season-actorlist', ]


class SeasonTestCaseMixin(TestCase):
    def setUp(self):
        self.client = AuthClient()
        self.season = SeasonFactory()


class AuthUserTest(SeasonTestCaseMixin):
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


class PowerUserTest(SeasonTestCaseMixin):
    def setUp(self):
        super(PowerUserTest, self).setUp()
        self.client = PowerUserAuthClient()

    def test_access_to_season_list(self):
        for symbolicurl in restrictedgenericurls:
            url = reverse(symbolicurl)
            # Final URL is forbidden
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)

    def test_access_to_season_detail(self):
        for symbolicurl in restrictedspecificurls:
            url = reverse(symbolicurl, kwargs={'pk': self.season.pk})
            # Final URL is forbidden
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)
