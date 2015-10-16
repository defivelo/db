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

from ..models import Organization


class OrgaBasicTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = AuthClient()

        self.orga = Organization.objects.create(name='Test-Orga',
                                                address_street='Street',
                                                address_no='42',
                                                address_zip='1234',
                                                address_city='City',
                                                address_canton='SG')

    def test_access_to_orga_list(self):
        # Issue a GET request.
        response = self.client.get(reverse('organization-list'))

        self.assertTemplateUsed(response, 'orga/organization_list.html')
        self.assertEqual(response.status_code, 200)

    def test_access_to_orga_detail(self):
        # Issue a GET request.
        response = self.client.get(reverse('organization-detail',
                                           kwargs={'pk': self.orga.pk}))

        self.assertTemplateUsed(response, 'orga/organization_detail.html')
        self.assertEqual(response.status_code, 200)

    def test_access_to_orga_edit(self):
        # Issue a GET request.
        response = self.client.get(reverse('organization-update',
                                           kwargs={'pk': self.orga.pk}))

        self.assertTemplateUsed(response, 'orga/organization_form.html')
        self.assertEqual(response.status_code, 200)
