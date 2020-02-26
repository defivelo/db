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

import datetime

from django.views.generic import ListView

from rolepermissions.mixins import HasPermissionsMixin

from defivelo.views import MenuView

from ..models import AnnualStateSetting


class AnnualStateSettingsListView(MenuView, HasPermissionsMixin, ListView):
    model = AnnualStateSetting
    context_object_name = "settings"
    ordering = ["canton"]
    required_permission = "settings_crud"

    def get_queryset(self):
        self.year = self.kwargs.pop("year", datetime.date.today().year)
        return super().get_queryset().filter(year=self.year)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["year"] = self.year
        return context
