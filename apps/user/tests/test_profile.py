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

from django.core.urlresolvers import NoReverseMatch, reverse
from django.test import TestCase

from defivelo.tests.utils import AuthClient, OfficeAuthClient

urlsforall = ['profile-update', 'user-detail', 'user-update' ]
urlsforoffice = ['user-list', 'user-list-export',]

def tryurl(symbolicurl, user):
    try:
        try:
            url = reverse(symbolicurl,
                          kwargs={'pk': user.pk}
                         )
        except NoReverseMatch:
            url = reverse(symbolicurl,
                          kwargs={'format': 'csv'}
                         )
    except NoReverseMatch:
        url = reverse(symbolicurl)
    return url


class AuthUserTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = AuthClient()

    def test_my_allowances(self):
        for symbolicurl in urlsforall:
            url = tryurl(symbolicurl, self.client.user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_my_restrictions(self):
        for symbolicurl in urlsforoffice:
            url = tryurl(symbolicurl, self.client.user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)


class OfficeUserTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = OfficeAuthClient()

    def test_my_allowances(self):
        for symbolicurl in urlsforall + urlsforoffice:
            response = self.client.get(tryurl(symbolicurl, self.client.user))
            self.assertEqual(response.status_code, 200)
