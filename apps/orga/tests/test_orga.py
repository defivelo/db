# -*- coding: utf-8 -*-
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
