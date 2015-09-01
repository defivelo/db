# -*- coding: utf-8 -*-
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
