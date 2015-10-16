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

from django.core.urlresolvers import reverse
from django.test import TestCase

from defivelo.tests.utils import AuthClient


class OrgaBasicTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = AuthClient()

    def test_access_to_profile(self):
        # Issue a GET request.
        response = self.client.get(reverse('profile-update'))

        self.assertTemplateUsed(response, 'auth/user_form.html')
        self.assertEqual(response.status_code, 200)
