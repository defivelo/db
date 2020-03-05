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

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from rolepermissions.mixins import HasPermissionsMixin

from apps.invoices.forms import InvoiceForm
from apps.invoices.models import Invoice
from apps.orga.models import Organization
from defivelo.roles import has_permission

from .mixins import CantonSeasonFormMixin
from .season import SeasonMixin


class InvoiceMixin(CantonSeasonFormMixin, HasPermissionsMixin):
    model = Invoice
    required_permission = "challenge_invoice_cru"
    context_object_name = "invoice"
    form_class = InvoiceForm

    def dispatch(self, request, *args, **kwargs):
        self.organization = get_object_or_404(
            Organization, pk=self.kwargs.get("orgapk")
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(organization=self.organization, season=self.season)
        )

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
        context["organization"] = self.organization
        return context

    def get_object(self):
        invoiceref = self.kwargs.get("invoiceref")

        return get_object_or_404(
            self.model,
            season=self.season,
            organization=self.organization,
            ref=invoiceref,
        )


class InvoiceDetailView(InvoiceMixin, DetailView):
    pass


class InvoiceCreateView(InvoiceMixin, CreateView):
    pass


class InvoiceListView(InvoiceMixin, ListView):
    context_object_name = "invoices"


class InvoiceUpdateView(InvoiceMixin, UpdateView):
    def get_form(self, *args, **kwargs):
        """
        Disallow any field edition if the field is locked
        """
        form = super().get_form(*args, **kwargs)
        if self.get_object().is_locked and not has_permission(
            self.request.user, "challenge_invoice_reset_to_draft"
        ):
            for field in form.fields:
                form.fields[field].disabled = True
        return form


class SeasonOrgaListView(SeasonMixin, HasPermissionsMixin, ListView):
    context_object_name = "organizations"
    required_permission = "challenge_invoice_cru"

    def get_queryset(self):
        return (
            Organization.objects.filter(sessions__in=self.season.sessions_with_qualifs)
            .annotate(nb_invoices=Count("invoices", distinct=True))
            .distinct()
        )
