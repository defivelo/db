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

from django.core.urlresolvers import reverse
from django.test import TestCase

from apps.common import DV_STATES
from defivelo.tests.utils import (
    AuthClient, PowerUserAuthClient, StateManagerAuthClient,
    SuperUserAuthClient,
)

from .factories import OrganizationFactory


class OrgaBasicTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = AuthClient()
        self.expected_code = 403
        self.expect_templates = False

        self.orga = OrganizationFactory()

    def test_access_to_orga_list(self):
        response = self.client.get(reverse('organization-list'))
        if self.expect_templates:
            self.assertTemplateUsed(response, 'orga/organization_filter.html')
        self.assertEqual(response.status_code, self.expected_code)

        response = self.client.get(reverse(
            'organization-list-export',
            kwargs={'format': 'csv'}))
        self.assertEqual(response.status_code, self.expected_code)

    def test_access_to_orga_detail(self):
        # Issue a GET request.
        response = self.client.get(reverse('organization-detail',
                                           kwargs={'pk': self.orga.pk}))

        if self.expect_templates:
            self.assertTemplateUsed(response, 'orga/organization_detail.html')
        self.assertEqual(response.status_code, self.expected_code)

    def test_access_to_orga_edit(self):
        # Issue a GET request.
        response = self.client.get(reverse('organization-update',
                                           kwargs={'pk': self.orga.pk}))

        if self.expect_templates:
            self.assertTemplateUsed(response, 'orga/organization_form.html')
        self.assertEqual(response.status_code, self.expected_code)

    def test_autocompletes(self):
        for al in ['OrganizationAutocomplete']:
            url = reverse(
                'autocomplete_light_autocomplete',
                kwargs={'autocomplete': al}
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, self.expected_code, url)


class OrgaPowerUserTest(OrgaBasicTest):
    def setUp(self):
        super(OrgaPowerUserTest, self).setUp()
        self.client = PowerUserAuthClient()
        self.expected_code = 200
        self.expect_templates = True


class SuperUserTest(OrgaBasicTest):
    def setUp(self):
        super(SuperUserTest, self).setUp()
        self.client = SuperUserAuthClient()
        self.expected_code = 200
        self.expect_templates = True
        self.orgas = [
            OrganizationFactory(address_canton=c)
            for c in DV_STATES]

    def test_autocompletes(self):
        for al in ['OrganizationAutocomplete']:
            url = reverse(
                'autocomplete_light_autocomplete',
                kwargs={'autocomplete': al}
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, self.expected_code, url)
            # Check that we only find our orga
            entries = [int(d) for d in
                       re.findall('data-value="(\d+)"', str(response.content))
                       ]
            entries.sort()
            self.assertEqual(
                entries,
                [self.orga.pk] + [o.pk for o in self.orgas]
            )


class OrgaStateManagerUserTest(TestCase):
    expected_code = 200

    def setUp(self):
        self.client = StateManagerAuthClient()
        mycanton = str((self.client.user.managedstates.first()).canton)
        self.myorga = OrganizationFactory(address_canton=mycanton)

        OTHERSTATES = [c for c in DV_STATES if c != mycanton]
        self.foreignorga = OrganizationFactory(
            address_canton=OTHERSTATES[0])

    def test_access_to_orga_list(self):
        response = self.client.get(reverse('organization-list'))
        self.assertTemplateUsed(response, 'orga/organization_filter.html')
        self.assertEqual(response.status_code, self.expected_code)

        response = self.client.get(reverse(
            'organization-list-export',
            kwargs={'format': 'csv'}))
        self.assertEqual(response.status_code, self.expected_code)

    def test_access_to_orga_detail(self):
        response = self.client.get(reverse('organization-detail',
                                           kwargs={'pk': self.myorga.pk}))
        self.assertTemplateUsed(response, 'orga/organization_detail.html')
        self.assertEqual(response.status_code, self.expected_code)

        # The other orga cannot be accessed
        response = self.client.get(reverse('organization-detail',
                                           kwargs={'pk': self.foreignorga.pk}))
        self.assertEqual(response.status_code, 404)

    def test_access_to_orga_edit(self):
        response = self.client.get(reverse('organization-update',
                                           kwargs={'pk': self.myorga.pk}))
        self.assertTemplateUsed(response, 'orga/organization_form.html')
        self.assertEqual(response.status_code, self.expected_code)

        # The other orga cannot be accessed
        response = self.client.get(reverse('organization-update',
                                           kwargs={'pk': self.foreignorga.pk}))
        self.assertEqual(response.status_code, 404)

    def test_autocompletes(self):
        for al in ['OrganizationAutocomplete']:
            url = reverse(
                'autocomplete_light_autocomplete',
                kwargs={'autocomplete': al}
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, self.expected_code, url)
            # Check that we only find our orga
            entries = re.findall('data-value="(\d+)"', str(response.content))
            self.assertEqual(entries, [str(self.myorga.pk)])
