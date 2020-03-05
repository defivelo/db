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

from defivelo.tests.utils import AuthClient, PowerUserAuthClient, StateManagerAuthClient

from ..models import Invoice
from .factories import InvoiceFactory
from .test_seasons import SeasonTestCaseMixin

season_urls = ["invoice-orga-list"]
invoice_list_urls = ["invoice-create", "invoice-list"]


class InvoiceTestCaseMixin(SeasonTestCaseMixin):
    def setUp(self):
        super().setUp()
        self.invoice = InvoiceFactory(
            season=self.season,
            organization=self.canton_orgas[0],
            status=Invoice.STATUS_DRAFT,
        )
        invoice_kwargs = {
            "seasonpk": self.invoice.season.pk,
            "orgapk": self.invoice.organization.pk,
            "invoiceref": self.invoice.ref,
        }

        self.invoice_update_url = reverse("invoice-update", kwargs=invoice_kwargs)
        self.invoice_detail_url = reverse("invoice-detail", kwargs=invoice_kwargs)


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

    def test_invoice_creation(self):
        kwargs = {
            "seasonpk": self.season.pk,
            "orgapk": self.canton_orgas[0].pk,
        }
        url = reverse("invoice-create", kwargs=kwargs,)
        initial = {"title": "Titolo", "status": Invoice.STATUS_DRAFT}

        response = self.client.post(url, initial)
        i = Invoice.objects.get(**initial)
        kwargs.update({"invoiceref": i.ref})
        self.assertRedirects(
            response, reverse("invoice-detail", kwargs=kwargs), target_status_code=200,
        )

    def test_invoice_update_title_only(self):
        """
        Updating a title only is OK
        """
        self.assertRedirects(
            self.client.post(
                self.invoice_update_url,
                {"title": "Titre du CdP", "status": self.invoice.status},
            ),
            self.invoice_detail_url,
            target_status_code=200,
        )

        i = Invoice.objects.get(ref=self.invoice.ref)
        self.assertEqual(i.title, "Titre du CdP", i)
        self.assertEqual(i.status, Invoice.STATUS_DRAFT, i)
        self.assertFalse(i.is_locked, i)

    def test_invoice_update_status_locks(self):
        """
        Updating the status away from DRAFT locks
        """
        # Maintenant passe la facture en "Validée"
        self.assertRedirects(
            self.client.post(
                self.invoice_update_url,
                {"title": "Titre 2 du CdP", "status": Invoice.STATUS_VALIDATED},
            ),
            self.invoice_detail_url,
            target_status_code=200,
        )

        i = Invoice.objects.get(ref=self.invoice.ref)
        self.assertEqual(i.title, "Titre 2 du CdP", i)
        self.assertEqual(i.status, Invoice.STATUS_VALIDATED)
        self.assertTrue(i.is_locked, i)

    def test_invoice_update_locked(self):
        """
        Updating a locked invoice fails
        """
        # Passe la facture en "Validée"
        self.invoice.status = Invoice.STATUS_VALIDATED
        self.invoice.save()
        self.assertTrue(self.invoice.is_locked, self.invoice)

        # Lea chargé de projet peut encore l'éditer
        self.assertEqual(self.client.get(self.invoice_update_url).status_code, 200)
        # Mais mettre à jour son statut échoue
        # Enfin. Ça marche, mais rien n'a changé
        self.assertRedirects(
            self.client.post(
                self.invoice_update_url,
                {"title": "Titre 3 du CdP", "status": Invoice.STATUS_DRAFT},
            ),
            self.invoice_detail_url,
            target_status_code=200,
        )

        # Elle n'est bien pas mise à jour
        i = Invoice.objects.get(ref=self.invoice.ref)
        self.assertNotEqual(i.title, "Titre 2 du CdP", i)
        self.assertEqual(i.status, Invoice.STATUS_VALIDATED)

        # Iel peut encore la voir
        self.assertEqual(
            self.client.get(self.invoice_detail_url).status_code, 200,
        )


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

    def test_invoice_creation(self):
        kwargs = {
            "seasonpk": self.season.pk,
            "orgapk": self.canton_orgas[0].pk,
        }
        url = reverse("invoice-create", kwargs=kwargs,)
        initial = {"title": "Titolo", "status": Invoice.STATUS_DRAFT}

        response = self.client.post(url, initial)
        i = Invoice.objects.get(**initial)
        kwargs.update({"invoiceref": i.ref})
        self.assertRedirects(
            response, reverse("invoice-detail", kwargs=kwargs), target_status_code=200,
        )

    def test_invoice_update_title_only(self):
        """
        Updating a title only is OK
        """
        self.assertRedirects(
            self.client.post(
                self.invoice_update_url,
                {"title": "Titre du CdP", "status": self.invoice.status},
            ),
            self.invoice_detail_url,
            target_status_code=200,
        )

        i = Invoice.objects.get(ref=self.invoice.ref)
        self.assertEqual(i.title, "Titre du CdP", i)
        self.assertEqual(i.status, Invoice.STATUS_DRAFT, i)
        self.assertFalse(i.is_locked, i)

    def test_invoice_update_status_locks(self):
        """
        Updating the status away from DRAFT locks
        """
        # Maintenant passe la facture en "Validée"
        self.assertRedirects(
            self.client.post(
                self.invoice_update_url,
                {"title": "Titre 2 du CdP", "status": Invoice.STATUS_VALIDATED},
            ),
            self.invoice_detail_url,
            target_status_code=200,
        )

        i = Invoice.objects.get(ref=self.invoice.ref)
        self.assertEqual(i.title, "Titre 2 du CdP", i)
        self.assertEqual(i.status, Invoice.STATUS_VALIDATED)
        self.assertTrue(i.is_locked, i)

    def test_invoice_update_locked(self):
        """
        Updating a locked invoice fails
        """
        # Passe la facture en "Validée"
        self.invoice.status = Invoice.STATUS_VALIDATED
        self.invoice.save()
        self.assertTrue(self.invoice.is_locked, self.invoice)

        # Lea burea peut encore l'éditer
        self.assertEqual(self.client.get(self.invoice_update_url).status_code, 200)
        # Et mettre à jour son statut, de retour vers Draft
        self.assertRedirects(
            self.client.post(
                self.invoice_update_url,
                {"title": "Titre 3 du Bureau", "status": Invoice.STATUS_DRAFT},
            ),
            self.invoice_detail_url,
            target_status_code=200,
        )
        # Elle est bien mise à jour
        i = Invoice.objects.get(ref=self.invoice.ref)
        self.assertNotEqual(i.title, "Titre 3 du bureau", i)
        self.assertEqual(i.status, Invoice.STATUS_DRAFT, i)
        self.assertFalse(i.is_locked, i)

        # Iel peut encore la voir
        self.assertEqual(
            self.client.get(self.invoice_detail_url).status_code, 200,
        )
