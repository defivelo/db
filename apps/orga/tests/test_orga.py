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

from django.test import TestCase
from django.urls import reverse

from apps.common import DV_STATES
from defivelo.tests.utils import (
    AuthClient,
    CoordinatorAuthClient,
    PowerUserAuthClient,
    StateManagerAuthClient,
    SuperUserAuthClient,
)

from ..models import Organization
from .factories import OrganizationFactory


class OrgaBasicTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = AuthClient()
        self.expected_code = 403
        self.expected_save_code = 403
        self.expect_templates = False

        self.orga = OrganizationFactory()
        self.orga.save()

    def test_access_to_orga_list(self):
        response = self.client.get(reverse("organization-list"))
        if self.expect_templates:
            self.assertTemplateUsed(response, "orga/organization_filter.html")
        self.assertEqual(response.status_code, self.expected_code)

        response = self.client.get(
            reverse("organization-list-export", kwargs={"format": "csv"})
        )
        self.assertEqual(response.status_code, self.expected_code)

    def test_access_to_orga_detail(self):
        # Issue a GET request.
        response = self.client.get(
            reverse("organization-detail", kwargs={"pk": self.orga.pk})
        )

        if self.expect_templates:
            self.assertTemplateUsed(response, "orga/organization_detail.html")
        self.assertEqual(response.status_code, self.expected_code)

    def test_access_to_orga_edit(self):
        url = reverse("organization-update", kwargs={"pk": self.orga.pk})
        response = self.client.get(url)

        if self.expect_templates:
            self.assertTemplateUsed(response, "orga/organization_form.html")
        self.assertEqual(response.status_code, self.expected_code)

    def test_autocompletes(self):
        url = reverse("organization-autocomplete")
        response = self.client.get(url)
        self.assertEqual(response.status_code, self.expected_code, url)


class OrgaPowerUserTest(OrgaBasicTest):
    def setUp(self):
        super(OrgaPowerUserTest, self).setUp()
        self.client = PowerUserAuthClient()
        self.expected_code = 200
        self.expected_save_code = 302
        self.expect_templates = True

    def test_access_to_orga_edit(self):
        url = reverse("organization-update", kwargs={"pk": self.orga.pk})
        super(OrgaPowerUserTest, self).test_access_to_orga_edit()

        self.orga.address_canton = "VD"
        self.orga.save()

        initial = self.orga.__dict__.copy()
        del initial["id"]
        del initial["created_on"]
        del initial["address_ptr_id"]
        del initial["_state"]

        # Test some update, that must go through
        initial["address_canton"] = "JU"

        for key in initial:
            initial[key] = "" if initial[key] == None else initial[key]

        response = self.client.post(url, initial)
        self.assertEqual(response.status_code, self.expected_save_code, url)

        neworga = Organization.objects.get(pk=self.orga.id)
        self.assertEqual(neworga.address_canton, "JU")


class SuperUserTest(OrgaBasicTest):
    def setUp(self):
        super(SuperUserTest, self).setUp()
        self.client = SuperUserAuthClient()
        self.expected_code = 200
        self.expected_save_code = 403
        self.expect_templates = True
        self.orgas = [OrganizationFactory(address_canton=c) for c in DV_STATES]

    def test_autocompletes(self):
        url = reverse("organization-autocomplete")
        response = self.client.get(url)
        self.assertEqual(response.status_code, self.expected_code, url)
        # Check that we only find our orga
        entries = [int(d) for d in re.findall(r'"id": "(\d+)"', str(response.content))]
        entries.sort()
        allentries = [self.orga.pk] + [o.pk for o in self.orgas]
        if re.search('"pagination": {"more": true}', str(response.content)):
            self.assertTrue(set(entries).issubset(allentries))
        else:
            self.assertEqual(entries, allentries)

    def test_accented_search(self):
        self.orga.abbr = "ÉCCG"
        self.orga.save()
        response = self.client.get("%s?%s" % (reverse("organization-list"), "q=eccg"))
        self.assertContains(response, "ÉCCG")


class OrgaStateManagerUserTest(TestCase):
    expected_code = 200

    def setUp(self):
        self.client = StateManagerAuthClient()
        mycanton = str((self.client.user.managedstates.first()).canton)
        self.myorga = OrganizationFactory(address_canton=mycanton)
        self.myorga.save()

        OTHERSTATES = [c for c in DV_STATES if c != mycanton]
        self.foreignorga = OrganizationFactory(address_canton=OTHERSTATES[0])
        self.foreignorga.save()

    def test_access_to_orga_list(self):
        response = self.client.get(reverse("organization-list"))
        self.assertTemplateUsed(response, "orga/organization_filter.html")
        self.assertEqual(response.status_code, self.expected_code)

        response = self.client.get(
            reverse("organization-list-export", kwargs={"format": "csv"})
        )
        self.assertEqual(response.status_code, self.expected_code)

    def test_access_to_orga_detail(self):
        response = self.client.get(
            reverse("organization-detail", kwargs={"pk": self.myorga.pk})
        )
        self.assertTemplateUsed(response, "orga/organization_detail.html")
        self.assertEqual(response.status_code, self.expected_code)

        # The other orga can also be accessed
        response = self.client.get(
            reverse("organization-detail", kwargs={"pk": self.foreignorga.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_access_to_orga_edit(self):
        url = reverse("organization-update", kwargs={"pk": self.myorga.pk})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "orga/organization_form.html")
        self.assertEqual(response.status_code, self.expected_code)

        # Our orga cannot be edited away from my cantons
        initial = self.myorga.__dict__.copy()
        del initial["id"]
        del initial["created_on"]
        del initial["address_ptr_id"]
        del initial["_state"]

        initial["address_no"] = self.myorga.address_no + 1

        for key in initial:
            initial[key] = "" if initial[key] == None else initial[key]

        response = self.client.post(url, initial)
        # Code 302 because update succeeded
        self.assertEqual(response.status_code, 302, url)
        # Check update succeeded
        neworga = Organization.objects.get(pk=self.myorga.pk)
        self.assertEqual(neworga.address_no, str(self.myorga.address_no + 1))

        # Test some update, that must go through
        initial["address_canton"] = self.foreignorga.address_canton

        response = self.client.post(url, initial)
        # Code 302 because silent update failed
        self.assertEqual(response.status_code, 302, url)
        # Check update failed
        neworga = Organization.objects.get(pk=self.myorga.pk)
        self.assertEqual(neworga.address_canton, self.myorga.address_canton)

        # The other orga cannot be accessed
        response = self.client.get(
            reverse("organization-update", kwargs={"pk": self.foreignorga.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_autocompletes(self):
        url = reverse("organization-autocomplete")
        response = self.client.get(url)
        self.assertEqual(response.status_code, self.expected_code, url)
        # Check that we find all orgas, including orgas of other cantons
        entries = re.findall(r'"id": "(\d+)"', str(response.content))
        expected_entries = set(str(o.id) for o in Organization.objects.all())
        self.assertEqual(set(entries), expected_entries)


class OrgaCoordinatorUserTest(TestCase):
    expected_code = 200

    def setUp(self):
        self.client = CoordinatorAuthClient()
        self.myorga = OrganizationFactory(coordinator=self.client.user)
        self.myorga.save()

        self.foreignorga = OrganizationFactory()
        self.foreignorga.save()

    def test_access_to_orga_list(self):
        response = self.client.get(reverse("organization-list"))
        self.assertTemplateUsed(response, "orga/organization_filter.html")
        self.assertEqual(response.status_code, self.expected_code)

        response = self.client.get(
            reverse("organization-list-export", kwargs={"format": "csv"})
        )
        self.assertEqual(response.status_code, self.expected_code)

    def test_access_to_orga_detail(self):
        response = self.client.get(
            reverse("organization-detail", kwargs={"pk": self.myorga.pk})
        )
        self.assertTemplateUsed(response, "orga/organization_detail.html")
        self.assertEqual(response.status_code, self.expected_code)

        # The other orga can also be accessed
        response = self.client.get(
            reverse("organization-detail", kwargs={"pk": self.foreignorga.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_access_to_orga_edit(self):
        url = reverse("organization-update", kwargs={"pk": self.myorga.pk})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "orga/organization_form.html")
        self.assertEqual(response.status_code, self.expected_code)

        # Our orga cannot be edited away from my cantons
        initial = self.myorga.__dict__.copy()
        del initial["id"]
        del initial["created_on"]
        del initial["address_ptr_id"]
        del initial["_state"]

        initial["address_no"] = self.myorga.address_no + 1

        for key in initial:
            initial[key] = "" if initial[key] == None else initial[key]

        response = self.client.post(url, initial)
        # Code 302 because update succeeded
        self.assertEqual(response.status_code, 302, url)
        # Check update succeeded
        neworga = Organization.objects.get(pk=self.myorga.pk)
        self.assertEqual(neworga.address_no, str(self.myorga.address_no + 1))

        # Test some update, that must go through
        initial["coordinator"] = self.client.user

        response = self.client.post(url, initial)
        # Check update failed
        neworga = Organization.objects.get(pk=self.myorga.pk)
        self.assertEqual(neworga.coordinator, self.myorga.coordinator)

        # The other orga cannot be accessed
        response = self.client.get(
            reverse("organization-update", kwargs={"pk": self.foreignorga.pk})
        )
        self.assertEqual(response.status_code, 404)
