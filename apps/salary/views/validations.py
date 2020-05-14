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

from datetime import date

from django.views.generic.dates import MonthArchiveView

from rolepermissions.mixins import HasPermissionsMixin

from defivelo.roles import user_cantons
from defivelo.views import MenuView

from ..models import MonthlyCantonalValidation


class ValidationsMixin(HasPermissionsMixin, MenuView):
    model = MonthlyCantonalValidation
    required_permission = "cantons_mine"
    context_object_name = "mcvs"
    date_field = "date"

    def dispatch(self, request, *args, **kwargs):
        self.year = int(kwargs.pop("year"))
        self.month = int(kwargs.pop("month"))
        self.managed_cantons = user_cantons(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Get the list of validations
        … but also make sure all the validations exist for that month and my cantons
        """
        qs = (
            super()
            .get_queryset()
            .filter(date__year=self.year, date__month=self.month)
            .order_by("canton")
        )
        available_mcvs = qs.values_list("canton", flat=True)
        need_creation = [c for c in self.managed_cantons if c not in available_mcvs]
        MonthlyCantonalValidation.objects.bulk_create(
            [
                MonthlyCantonalValidation(canton=c, date=date(self.year, self.month, 1))
                for c in need_creation
            ]
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] = "finance"
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["year"] = self.year
        form_kwargs["month"] = self.month
        return form_kwargs

    def get_success_url(self):
        return reverse_lazy("validations-list", kwargs={"year": self.object.year})


class ValidationsMonthView(ValidationsMixin, MonthArchiveView):
    allow_future = True
    allow_empty = True


# class AnnualStateSettingMixin(ValidationsMixin, SuccessMessageMixin, MenuView):
#     context_object_name = "setting"
#     form_class = AnnualStateSettingForm


# class AnnualStateSettingCreateView(AnnualStateSettingMixin, CreateView):
#     success_message = _("Configuration cantonale par année créée")


# class AnnualStateSettingUpdateView(AnnualStateSettingMixin, UpdateView):
#     success_message = _("Configuration cantonale par année mise à jour")
