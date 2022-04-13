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

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView

from rolepermissions.mixins import HasPermissionsMixin

from apps.common import DV_STATES
from defivelo.roles import has_permission
from defivelo.views import MenuView

from ..forms import AnnualStateSettingForm
from ..models import AnnualStateSetting


class SettingsMixin(HasPermissionsMixin):
    model = AnnualStateSetting
    required_permission = "settings_crud"

    def dispatch(self, request, *args, **kwargs):
        self.year = kwargs.pop("year")
        self.cantons = (
            DV_STATES
            if has_permission(request.user, "cantons_all")
            else self.request.user.managedstates.all().values_list("canton", flat=True)
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(year=self.year, canton__in=self.cantons)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] = "settings"
        context["year"] = self.year
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["year"] = self.year
        form_kwargs["cantons"] = self.cantons
        return form_kwargs

    def get_success_url(self):
        return reverse_lazy(
            "annualstatesettings-list", kwargs={"year": self.object.year}
        )


class AnnualStateSettingsListView(SettingsMixin, MenuView, ListView):
    context_object_name = "settings"
    ordering = ["canton"]


class AnnualStateSettingMixin(SettingsMixin, SuccessMessageMixin, MenuView):
    context_object_name = "setting"
    form_class = AnnualStateSettingForm


class AnnualStateSettingCreateView(AnnualStateSettingMixin, CreateView):
    success_message = _("Configuration cantonale par année créée")


class AnnualStateSettingUpdateView(AnnualStateSettingMixin, UpdateView):
    success_message = _("Configuration cantonale par année mise à jour")
