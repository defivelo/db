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
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import UpdateView

from rolepermissions.mixins import HasPermissionsMixin

from apps.invoices.forms import CreateInvoiceForm
from apps.invoices.models import Invoice

from .mixins import CantonSeasonFormMixin


class InvoiceMixin(CantonSeasonFormMixin, HasPermissionsMixin):
    model = Invoice
    required_permission = "challenge_invoice_crud"
    context_object_name = "invoice"

    def get_form_kwargs(self, **kwargs):
        kw = super().get_form_kwargs(**kwargs)
        kw.pop("cantons")
        kw["organization"] = kw["instance"].organization
        # assert False, kw
        return kw

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] = "season"
        context["season"] = self.season
        return context

    def get_object(self):
        resolvermatch = self.request.resolver_match
        organization_id = int(resolvermatch.kwargs.get("orgapk"))

        Invoice = self.model
        try:
            invoice = Invoice.objects.get(
                season=self.season, organization_id=organization_id
            )
        except Invoice.DoesNotExist:
            invoice = Invoice(season=self.season, organization_id=organization_id)
            for refid in range(100, 999):
                invoice.ref = f"DV{self.season.year % 100}{refid:03d}"
                try:
                    invoice.validate_unique()
                    # If unicity is garanteed, proceed
                    break
                except ValidationError:
                    # Try another number
                    pass
            else:
                # This should not happen.
                raise Exception(
                    _(
                        f"Épuisé l'espace des factures établissements pour l'année {self.season.year} avec l'identifiant {invoice.ref}."
                    )
                )

            invoice.save()
        return invoice

    def get_success_url(self):
        return reverse_lazy("season-detail", kwargs={"pk": self.season.pk})


class InvoiceUpdateView(InvoiceMixin, UpdateView):
    form_class = CreateInvoiceForm
