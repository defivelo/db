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

from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django_filters import CharFilter, FilterSet
from django_filters.views import FilterView
from filters.views import FilterMixin

from defivelo.views import MenuView

from .forms import OrganizationForm
from .models import Organization


class OrganizationFilterSet(FilterSet):
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

    q = CharFilter(
        label=_('Recherche'),
        action=filter_wide
    )

    class Meta:
        model = Organization
        fields = ['q']


class OrganizationMixin(MenuView):
    model = Organization
    context_object_name = 'organization'
    form_class = OrganizationForm

    def get_context_data(self, **kwargs):
        context = super(OrganizationMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'organization'
        return context


class OrganizationsListView(OrganizationMixin,
                            FilterMixin, FilterView):
    filterset_class = OrganizationFilterSet
    context_object_name = 'organizations'

    def get_queryset(self):
        return Organization.objects.all()


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
