# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015 Didier Raboud <me+defivelo@odyx.org>
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
from __future__ import unicode_literals

import operator
from functools import reduce

from autocomplete_light import AutocompleteModelBase, register as al_register
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django_filters import CharFilter, FilterSet, MultipleChoiceFilter
from django_filters.views import FilterView
from filters.views import FilterMixin
from rolepermissions.mixins import HasPermissionsMixin
from rolepermissions.shortcuts import get_user_role
from rolepermissions.verifications import has_permission

from apps.common import DV_STATE_CHOICES_WITH_DEFAULT
from apps.common.views import ExportMixin
from defivelo.roles import StateManager
from defivelo.views import MenuView

from .export import OrganizationResource
from .forms import OrganizationForm
from .models import Organization


class OrganizationFilterSet(FilterSet):
    def __init__(self, cantons=None, **kwargs):
        super(OrganizationFilterSet, self).__init__(**kwargs)
        if cantons:
            if len(cantons) > 1:
                choices = self.filters['address_canton'].extra['choices']
                choices = (
                    (k, v) for (k, v)
                    in choices
                    if k in cantons or not k
                )
                self.filters['address_canton'].extra['choices'] = choices
            elif len(cantons) == 1:
                del(self.filters['address_canton'])

    def filter_wide(queryset, value):
        if value:
            allfields_filter = [
                Q(name__icontains=value),
                Q(address_street__icontains=value),
                Q(address_zip__contains=value),
                Q(address_city__icontains=value),
            ]
            return queryset.filter(reduce(operator.or_, allfields_filter))
        return queryset

    address_canton = MultipleChoiceFilter(
        label=_("Cantons"),
        choices=DV_STATE_CHOICES_WITH_DEFAULT,
    )

    q = CharFilter(
        label=_('Recherche'),
        action=filter_wide
    )

    class Meta:
        model = Organization
        fields = ['q', 'address_canton', ]


class OrganizationMixin(HasPermissionsMixin, MenuView):
    required_permission = 'orga_crud'
    model = Organization
    context_object_name = 'organization'
    form_class = OrganizationForm

    def get_cantons(self):
        if get_user_role(self.request.user) == StateManager:
            return [
                m.canton for m in self.request.user.managedstates.all()
            ]

    def get_queryset(self):
        qs = self.model.objects
        usercantons = self.get_cantons()
        if usercantons:
            qs = qs.filter(address_canton__in=usercantons)
        else:
            qs = qs.all()
        return qs

    def get_form_kwargs(self):
        kwargs = super(OrganizationMixin, self).get_form_kwargs()
        kwargs['cantons'] = self.get_cantons()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OrganizationMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'organization'
        return context


class OrganizationsListView(OrganizationMixin,
                            FilterMixin, FilterView):
    filterset_class = OrganizationFilterSet
    context_object_name = 'organizations'

    def get_filterset_kwargs(self, filterset_class):
        kwargs = (
            super(OrganizationsListView, self)
            .get_filterset_kwargs(filterset_class)
        )
        usercantons = self.get_cantons()
        if usercantons:
            kwargs['cantons'] = usercantons
        return kwargs


class OrganizationDetailView(OrganizationMixin,
                             DetailView):
    pass


class OrganizationUpdateView(OrganizationMixin,
                             SuccessMessageMixin,
                             UpdateView):
    success_message = _("Établissement mis à jour")


class OrganizationCreateView(OrganizationMixin,
                             SuccessMessageMixin,
                             CreateView):
    success_message = _("Établissement créé")


class OrganizationDeleteView(OrganizationMixin, DeleteView):
    success_url = reverse_lazy('organization-list')


class OrganizationListExport(ExportMixin, OrganizationsListView):
    export_class = OrganizationResource()
    export_filename = _('Établissements')


class OrganizationAutocomplete(OrganizationMixin, AutocompleteModelBase):
    search_fields = ['name', 'address_city', 'address_street']
    required_permission = 'orga_crud'

    def choices_for_request(self):
        self.choices = self.get_queryset()
        if has_permission(self.request.user, self.required_permission):
            return super(OrganizationAutocomplete, self).choices_for_request()
        else:
            raise PermissionDenied

al_register(OrganizationAutocomplete)
