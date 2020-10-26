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

from datetime import date, time, timedelta

from django.urls import reverse

from defivelo.tests.utils import AuthClient, PowerUserAuthClient, StateManagerAuthClient

from ..models import Invoice
from .factories import InvoiceFactory, InvoiceLineFactory
from .test_seasons import SeasonTestCaseMixin

season_urls = ["invoice-orga-list"]
invoice_list_urls = ["invoice-create", "invoice-list"]


def test_invoiceline_out_of_date(db):
    invoiceline = InvoiceLineFactory()
    # Make sure it is not up-to-date
    invoiceline.nb_bikes = invoiceline.session.n_bikes + 1
    assert not invoiceline.is_up_to_date
    invoiceline.refresh()
    assert invoiceline.is_up_to_date


def test_invoiceline_without_session_is_always_out_of_date(db):
    invoiceline = InvoiceLineFactory()
    # Make sure it is not up-to-date by deleting its Session
    invoiceline.session = None
    assert not invoiceline.is_up_to_date
    invoiceline.refresh()
    # It can't become up_to_date
    assert not invoiceline.is_up_to_date


def test_invoice_out_of_date(db):
    invoice = InvoiceFactory()
    # Create 1+2+3+4+5 invoicelines to test all possible sequences
    invoicelines = [InvoiceLineFactory(invoice=invoice) for i in range(0, 15)]

    # Make sure it cannot be up-to-date
    invoicelines[0].nb_bikes = invoicelines[0].session.n_bikes + 1
    assert not invoice.is_up_to_date

    # Now align it all
    invoice.organization.address_canton = invoice.season.cantons.split("|")[0]
    invoice.organization.save()
    # This is a quick-fix for SeasonFactory that puts a single canton instead of an array
    invoice.season.cantons = [invoice.season.cantons]
    invoice.season.save()
    # Create a 1-block, then a space, then a 2-block, then a space, etc
    dayshift = 0
    nth_in_sequence = 1
    sequence_max = 1
    for il in invoicelines:
        il.session.orga = invoice.organization
        # Test the sequences too
        il.session.day = invoice.season.begin + timedelta(days=dayshift)
        if nth_in_sequence < sequence_max:
            nth_in_sequence = nth_in_sequence + 1
        elif nth_in_sequence >= sequence_max:
            nth_in_sequence = 1
            sequence_max = sequence_max + 1
            dayshift = dayshift + 1
        dayshift = dayshift + 1
        il.session.save()
        il.refresh()
        assert il.is_up_to_date
        il.save()
    assert invoice.is_up_to_date

    nth_in_sequence = 1
    sequence_max = 1
    # We have 5 invoicelines, the deduction is 30% for all
    for il in invoicelines:
        if sequence_max == 1:
            assert il.cost_bikes_reduction_percent() == 0
        if sequence_max == 2:
            assert il.cost_bikes_reduction_percent() == 5
        if sequence_max == 3:
            assert il.cost_bikes_reduction_percent() == 10
        if sequence_max == 4:
            assert il.cost_bikes_reduction_percent() == 20
        if sequence_max == 5:
            assert il.cost_bikes_reduction_percent() == 30
        if nth_in_sequence < sequence_max:
            nth_in_sequence = nth_in_sequence + 1
        elif nth_in_sequence >= sequence_max:
            nth_in_sequence = 1
            sequence_max = sequence_max + 1


def test_bikes_are_accounted_once_per_day(db):
    invoice = InvoiceFactory()
    line_am = InvoiceLineFactory(
        invoice=invoice,
        nb_bikes=10,
        session__day=date(2020, 1, 1),
        session__begin=time(8, 30),
    )
    line_pm = InvoiceLineFactory(
        invoice=invoice,
        nb_bikes=10,
        session__day=date(2020, 1, 1),
        session__begin=time(13, 30),
    )
    assert not line_am.has_cost_bikes and line_am.cost_bikes_reduced == 0
    assert line_pm.has_cost_bikes and line_pm.cost_bikes_reduced > 0

    previous_sum_cost = invoice.sum_cost()
    line_am.cost_bikes = 0
    line_am.save()
    assert invoice.sum_cost() == previous_sum_cost
    line_pm.cost_bikes = 0
    line_pm.save()
    assert invoice.sum_cost() < previous_sum_cost


def test_bikes_are_accounted_for_the_session_with_most_bikes(db):
    invoice = InvoiceFactory()
    line_am = InvoiceLineFactory(
        invoice=invoice,
        nb_bikes=11,
        session__day=date(2020, 1, 1),
        session__begin=time(8, 30),
    )
    line_pm = InvoiceLineFactory(
        invoice=invoice,
        nb_bikes=10,
        session__day=date(2020, 1, 1),
        session__begin=time(13, 30),
    )
    assert line_am.has_cost_bikes and line_am.cost_bikes_reduced > 0
    assert not line_pm.has_cost_bikes and line_pm.cost_bikes_reduced == 0


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

    def test_access_to_yearly_urls(self):
        url = reverse("invoices-yearly-list", kwargs={"year": 2020})
        response = self.client.get(url)
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

    def test_access_to_yearly_urls(self):
        url = reverse("invoices-yearly-list", kwargs={"year": 2020})
        response = self.client.get(url)
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
        url = reverse(
            "invoice-create",
            kwargs=kwargs,
        )
        initial = {"title": "Titolo", "status": Invoice.STATUS_DRAFT}

        response = self.client.post(url, initial)
        i = Invoice.objects.get(**initial)
        kwargs.update({"invoiceref": i.ref})
        self.assertRedirects(
            response,
            reverse("invoice-detail", kwargs=kwargs),
            target_status_code=200,
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
            self.client.get(self.invoice_detail_url).status_code,
            200,
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

    def test_access_to_yearly_urls(self):
        url = reverse("invoices-yearly-list", kwargs={"year": 2020})
        response = self.client.get(url)
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
        url = reverse(
            "invoice-create",
            kwargs=kwargs,
        )
        initial = {"title": "Titolo", "status": Invoice.STATUS_DRAFT}

        response = self.client.post(url, initial)
        i = Invoice.objects.get(**initial)
        kwargs.update({"invoiceref": i.ref})
        self.assertRedirects(
            response,
            reverse("invoice-detail", kwargs=kwargs),
            target_status_code=200,
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
            self.client.get(self.invoice_detail_url).status_code,
            200,
        )
