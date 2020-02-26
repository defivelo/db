# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2020 Didier 'OdyX' Raboud <didier.raboud@liip.ch>
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

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.challenge.models import AnnualStateSetting
from defivelo.tests.utils import AuthClient, PowerUserAuthClient, StateManagerAuthClient

from .test_seasons import SeasonTestCaseMixin


class SettingTestCase(TestCase):
    def test_settings_no_negative_costs(self):
        s0 = AnnualStateSetting(year=2020, canton="VD", cost_per_bike=-12)
        with self.assertRaises(expected_exception=ValidationError):
            s0.full_clean()

        s1 = AnnualStateSetting(year=2020, canton="VD", cost_per_participant=-12)
        with self.assertRaises(expected_exception=ValidationError):
            s1.full_clean()

    def test_settings_unique_together(self):
        s0 = AnnualStateSetting(year=2020, canton="VD")
        s0.save()
        s1 = AnnualStateSetting(year=2020, canton="VD")
        with self.assertRaises(expected_exception=ValidationError):
            s1.full_clean()
        with self.assertRaisesMessage(
            expected_exception=IntegrityError,
            expected_message="duplicate key value violates unique constraint",
        ):
            s1.save()


class AuthUserTest(SeasonTestCaseMixin):
    def setUp(self):
        self.client = AuthClient()
        super().setUp()

    def test_settings_list_access(self):
        url = reverse("annualstatesettings-list")
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse("annualstatesettings-list", kwargs={"year": timezone.now().year}),
            target_status_code=403,
        )

        url = reverse("annualstatesettings-list", kwargs={"year": 2019})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, url)


class StateManagerUserTest(SeasonTestCaseMixin):
    def setUp(self):
        self.client = StateManagerAuthClient()
        super().setUp()

    def test_settings_list_access(self):
        url = reverse("annualstatesettings-list")
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse("annualstatesettings-list", kwargs={"year": timezone.now().year}),
            target_status_code=403,
        )

        url = reverse("annualstatesettings-list", kwargs={"year": 2019})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, url)


class PowerUserTest(SeasonTestCaseMixin):
    def setUp(self):
        self.client = PowerUserAuthClient()
        super().setUp()

    def test_settings_list_access(self):
        url = reverse("annualstatesettings-list")
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse("annualstatesettings-list", kwargs={"year": timezone.now().year}),
        )

        url = reverse("annualstatesettings-list", kwargs={"year": 2019})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
