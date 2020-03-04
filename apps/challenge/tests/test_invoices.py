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

from django.urls import reverse

from apps.invoices.tests.factories import InvoiceFactory
from defivelo.tests.utils import AuthClient, PowerUserAuthClient, StateManagerAuthClient

from .test_seasons import SeasonTestCaseMixin

season_urls = ["invoice-orga-list"]
invoice_list_urls = ["invoice-create", "invoice-list"]


class InvoiceTestCaseMixin(SeasonTestCaseMixin):
    def setUp(self):
        super().setUp()
        self.invoice = InvoiceFactory(
            season=self.season, organization=self.canton_orgas[0]
        )
        self.invoice.save()


class AuthUserTest(InvoiceTestCaseMixin):
    def setUp(self):
        self.client = AuthClient()
        super().setUp()

    def test_access_to_season_urls(self):
        for symbolicurl in season_urls:
            url = reverse(symbolicurl, kwargs={"seasonpk": self.season.pk})
            response = self.client.get(url, follow=True)
            # No access
            self.assertEqual(response.status_code, 403, url)

    def test_access_to_invoice_lists(self):
        for symbolicurl in invoice_list_urls:
            url = reverse(
                symbolicurl,
                kwargs={"seasonpk": self.season.pk, "orgapk": self.canton_orgas[0].pk},
            )
            response = self.client.get(url, follow=True)
            # No access
            self.assertEqual(response.status_code, 403, url)

    def test_access_to_invoice(self):
        url = reverse(
            "invoice-detail",
            kwargs={
                "seasonpk": self.season.pk,
                "orgapk": self.canton_orgas[0].pk,
                "invoiceref": self.invoice.ref,
            },
        )
        response = self.client.get(url, follow=True)
        # No access
        self.assertEqual(response.status_code, 403, url)


class StateManagerUserTest(InvoiceTestCaseMixin):
    def setUp(self):
        self.client = StateManagerAuthClient()
        super().setUp()

    def test_access_to_season_urls(self):
        for symbolicurl in season_urls:
            url = reverse(symbolicurl, kwargs={"seasonpk": self.season.pk})
            # Final URL is OK
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)

    def test_access_to_invoice_lists(self):
        for symbolicurl in invoice_list_urls:
            url = reverse(
                symbolicurl,
                kwargs={"seasonpk": self.season.pk, "orgapk": self.canton_orgas[0].pk},
            )
            response = self.client.get(url, follow=True)
            # Final URL is OK
            self.assertEqual(response.status_code, 200, url)

    def test_access_to_invoice(self):
        url = reverse(
            "invoice-detail",
            kwargs={
                "seasonpk": self.season.pk,
                "orgapk": self.canton_orgas[0].pk,
                "invoiceref": self.invoice.ref,
            },
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, url)


class PowerUserTest(InvoiceTestCaseMixin):
    def setUp(self):
        self.client = PowerUserAuthClient()
        super().setUp()

    def test_access_to_season_urls(self):
        for symbolicurl in season_urls:
            url = reverse(symbolicurl, kwargs={"seasonpk": self.season.pk})
            # Final URL is OK
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)

    def test_access_to_invoice_lists(self):
        for symbolicurl in invoice_list_urls:
            url = reverse(
                symbolicurl,
                kwargs={"seasonpk": self.season.pk, "orgapk": self.canton_orgas[0].pk},
            )
            response = self.client.get(url, follow=True)
            # Final URL is OK
            self.assertEqual(response.status_code, 200, url)

    def test_access_to_invoice(self):
        url = reverse(
            "invoice-detail",
            kwargs={
                "seasonpk": self.season.pk,
                "orgapk": self.canton_orgas[0].pk,
                "invoiceref": self.invoice.ref,
            },
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, url)
