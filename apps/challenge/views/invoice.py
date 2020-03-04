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

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from rolepermissions.mixins import HasPermissionsMixin

from apps.invoices.forms import InvoiceForm
from apps.invoices.models import Invoice
from apps.orga.models import Organization
from defivelo.roles import has_permission

from .mixins import CantonSeasonFormMixin


class InvoiceMixin(CantonSeasonFormMixin, HasPermissionsMixin):
    model = Invoice
    required_permission = "challenge_invoice_cru"
    context_object_name = "invoice"
    form_class = InvoiceForm

    @cached_property
    def organization(self):
        orgapk = int(self.kwargs.get("orgapk"))
        return get_object_or_404(Organization, pk=orgapk)

    def get_form_kwargs(self, **kwargs):
        kw = super().get_form_kwargs(**kwargs)
        # Remove cantons, we don't need them.
        kw.pop("cantons")
        kw["organization"] = self.organization
        return kw

    def get_initial(self, **kwargs):
        kw = super().get_initial(**kwargs)
        kw["organization"] = self.organization
        kw["season"] = self.season
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
        invoiceref = resolvermatch.kwargs.get("invoiceref")

        return get_object_or_404(
            self.model,
            season=self.season,
            organization_id=organization_id,
            ref=invoiceref,
        )


class InvoiceDetailView(InvoiceMixin, DetailView):
    pass


class InvoiceCreateView(InvoiceMixin, CreateView):
    pass


class InvoiceUpdateView(InvoiceMixin, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        """
        Disallow update when the state is not draft anymore, and the rights are not granted
        """
        invoice = self.get_object()
        if invoice.is_locked:
            if not has_permission(request.user, "challenge_invoice_reset_to_draft"):
                raise PermissionDenied
        else:
            if not has_permission(request.user, "challenge_invoice_cru"):
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
