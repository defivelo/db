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

from factory import fuzzy

from apps.challenge.models import AnnualStateSetting
from apps.common import DV_STATES
from defivelo.tests.utils import AuthClient, PowerUserAuthClient, StateManagerAuthClient

from .factories import AnnualStateSettingFactory
from .test_seasons import SeasonTestCaseMixin


class SettingTestCase(TestCase):
    def setUp(self):
        self.year = fuzzy.FuzzyInteger(1999, 2050).fuzz()
        self.canton = fuzzy.FuzzyChoice(DV_STATES).fuzz()

    def test_settings_no_negative_costs(self):
        s0 = AnnualStateSetting(
            year=self.year,
            canton=self.canton,
            cost_per_bike=fuzzy.FuzzyInteger(-100, -1).fuzz(),
        )
        with self.assertRaises(expected_exception=ValidationError):
            s0.full_clean()

        s1 = AnnualStateSetting(
            year=self.year,
            canton=self.canton,
            cost_per_participant=fuzzy.FuzzyInteger(-100, -1).fuzz(),
        )
        with self.assertRaises(expected_exception=ValidationError):
            s1.full_clean()

    def test_settings_unique_together(self):
        s0 = AnnualStateSetting(year=self.year, canton=self.canton)
        s0.save()
        s1 = AnnualStateSetting(year=self.year, canton=self.canton)
        with self.assertRaises(expected_exception=ValidationError):
            s1.full_clean()
        with self.assertRaisesMessage(
            expected_exception=IntegrityError,
            expected_message="duplicate key value violates unique constraint",
        ):
            s1.save()


class SettingsViewsTestCase(SeasonTestCaseMixin):
    def setUp(self):
        """
        Prepare the URLs
        """
        super().setUp()
        self.url_yearly = reverse(
            "annualstatesettings-list",
            kwargs={"year": fuzzy.FuzzyInteger(1999, 2050).fuzz()},
        )
        self.create_initial = {
            "year": fuzzy.FuzzyInteger(1999, 2050).fuzz(),
            "canton": fuzzy.FuzzyChoice(DV_STATES).fuzz(),
            "cost_per_bike": fuzzy.FuzzyInteger(0, 100).fuzz(),
            "cost_per_participant": fuzzy.FuzzyInteger(0, 100).fuzz(),
        }
        self.url_create = reverse(
            "annualstatesetting-create",
            kwargs={"year": self.create_initial["year"]},
        )

        self.setting = AnnualStateSettingFactory()
        self.setting.save()

        self.url_update = reverse(
            "annualstatesetting-update",
            kwargs={"year": self.setting.year, "pk": self.setting.pk},
        )
        self.restricted_urls = [self.url_yearly, self.url_create, self.url_update]


class AuthUserTest(SettingsViewsTestCase):
    def setUp(self):
        self.client = AuthClient()
        super().setUp()

    def test_settings_list_access(self):
        for url in self.restricted_urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)


class StateManagerUserTest(SettingsViewsTestCase):
    def setUp(self):
        self.client = StateManagerAuthClient()
        super().setUp()

    def test_no_access_to_foreignsettings(self):
        # Make the setting _not_ an accessible setting
        foreignsetting = AnnualStateSettingFactory(
            canton=next(
                c
                for c in DV_STATES
                if c
                not in self.client.user.managedstates.all().values_list(
                    "canton", flat=True
                )
            )
        )
        foreignsetting.save()

        # The StateManager can't access other canton's settings
        url = reverse(
            "annualstatesetting-update",
            kwargs={"year": foreignsetting.year, "pk": foreignsetting.pk},
        )
        self.assertEqual(self.client.get(url).status_code, 404, url)

    def test_create_setting_in_our_cantons(self):
        # Now create one in our cantons, and ensure we return on the page that corresponds to our year
        initial = self.create_initial
        initial["year"] = 1968
        initial["canton"] = self.client.user.managedstates.first().canton
        self.assertRedirects(
            self.client.post(self.url_create, initial),
            reverse(
                "annualstatesettings-list",
                kwargs={"year": 1968},
            ),
            target_status_code=200,
        )

    def test_update_setting_in_our_cantons(self):
        setting = AnnualStateSettingFactory(
            canton=self.client.user.managedstates.first().canton
        )
        setting.save()

        update_url = reverse(
            "annualstatesetting-update",
            kwargs={"year": setting.year, "pk": setting.pk},
        )

        initial = setting.__dict__
        initial["year"] = 2021

        # On update, ensure we return on the page that corresponds to our new year
        self.assertRedirects(
            self.client.post(update_url, initial),
            reverse(
                "annualstatesettings-list",
                kwargs={"year": 2021},
            ),
            target_status_code=200,
        )


class PowerUserTest(SettingsViewsTestCase):
    def setUp(self):
        self.client = PowerUserAuthClient()
        super().setUp()

    def test_settings_list_access(self):
        # The restricted urls are allowed to power user
        for url in self.restricted_urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)

        # On create, ensure we return on the page that corresponds to our year
        initial = self.create_initial
        initial["year"] = 1968
        self.assertRedirects(
            self.client.post(self.url_create, self.create_initial),
            reverse(
                "annualstatesettings-list",
                kwargs={"year": 1968},
            ),
            target_status_code=200,
        )
        initial = self.setting.__dict__
        initial["year"] = 1968

        # On update, ensure we return on the page that corresponds to our new year
        self.assertRedirects(
            self.client.post(self.url_update, initial),
            reverse(
                "annualstatesettings-list",
                kwargs={"year": 1968},
            ),
            target_status_code=200,
        )
