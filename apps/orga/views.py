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

import operator
from functools import reduce

from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from dal_select2.views import Select2QuerySetView
from django_filters import CharFilter, FilterSet, MultipleChoiceFilter
from django_filters.views import FilterView
from rolepermissions.checkers import has_role
from rolepermissions.mixins import HasPermissionsMixin

from apps.common import DV_STATE_CHOICES_WITH_DEFAULT
from apps.common.views import ExportMixin, PaginatorMixin
from defivelo.roles import has_permission, user_cantons
from defivelo.views import MenuView

from .export import OrganizationResource
from .forms import OrganizationForm
from .models import ORGASTATUS_ACTIVE, ORGASTATUS_CHOICES, Organization


class OrganizationFilterSet(FilterSet):
    def __init__(self, data=None, *args, **kwargs):
        any_filter_is_set = bool(set(self.base_filters) & set(data or {}))
        if not any_filter_is_set:
            data = {}
            for name, f in self.base_filters.items():
                initial = f.extra.get("initial")
                # filter param is either missing or empty, use initial as default
                if not data.get(name) and initial:
                    data[name] = initial

        super(OrganizationFilterSet, self).__init__(data, *args, **kwargs)

    def filter_wide(queryset, name, value):
        if value:
            allfields_filter = [
                Q(name__unaccent__icontains=value),
                Q(abbr__unaccent__icontains=value),
                Q(address_street__unaccent__icontains=value),
                Q(address_zip__contains=value),
                Q(address_city__unaccent__icontains=value),
            ]
            return queryset.filter(reduce(operator.or_, allfields_filter))
        return queryset

    address_canton = MultipleChoiceFilter(
        label=_("Cantons"),
        choices=DV_STATE_CHOICES_WITH_DEFAULT,
    )

    status = MultipleChoiceFilter(
        label=_("Statut"),
        choices=ORGASTATUS_CHOICES,
        initial=[
            ORGASTATUS_ACTIVE,
        ],
    )

    q = CharFilter(label=_("Recherche"), method=filter_wide)

    class Meta:
        model = Organization
        fields = [
            "q",
            "status",
            "address_canton",
        ]


class OrganizationDetailMixin(HasPermissionsMixin, MenuView):
    required_permission = "orga_show"
    model = Organization
    context_object_name = "organization"

    def get_context_data(self, **kwargs):
        context = super(OrganizationDetailMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] = "organization"
        return context


class OrganizationDetailView(OrganizationDetailMixin, DetailView):
    pass


class OrganizationsListView(OrganizationDetailMixin, PaginatorMixin, FilterView):
    filterset_class = OrganizationFilterSet
    context_object_name = "organizations"


class OrganizationListExport(ExportMixin, OrganizationsListView):
    export_class = OrganizationResource()
    export_filename = _("Établissements")


class OrganizationAutocomplete(OrganizationDetailMixin, Select2QuerySetView):
    required_permission = "orga_detail_all"

    def get_queryset(self):
        if has_permission(self.request.user, self.required_permission):
            qs = super(OrganizationAutocomplete, self).get_queryset()
            if self.q:
                qs = OrganizationFilterSet.filter_wide(qs, "", self.q)
            return qs
        else:
            raise PermissionDenied


class OrganizationCrudMixin(OrganizationDetailMixin):
    required_permission = "orga_crud"
    form_class = OrganizationForm

    def get_queryset(self):
        if self.request.user.managed_organizations.count():
            return self.request.user.managed_organizations
        qs = self.model.objects
        try:
            usercantons = user_cantons(self.request.user)
        except LookupError:
            raise PermissionDenied
        if usercantons:
            qs = qs.filter(address_canton__in=usercantons)
        return qs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            kwargs["cantons"] = user_cantons(self.request.user)
        except LookupError:
            kwargs["cantons"] = [
                orga.address_canton
                for orga in self.request.user.managed_organizations.all()
            ]
        return kwargs

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if has_role(self.request.user, "coordinator") and not has_role(
            self.request.user, "power_user"
        ):
            form.fields["status"].disabled = True
            form.fields["coordinator"].disabled = True
            del form.fields["comments"]
        if not has_permission(self.request.user, "orga_edit_address"):
            form.fields["address_canton"].disabled = True
        return form


class OrganizationUpdateView(OrganizationCrudMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Établissement mis à jour")
    required_permission = "orga_edit"


class OrganizationCreateView(OrganizationCrudMixin, SuccessMessageMixin, CreateView):
    success_message = _("Établissement créé")
