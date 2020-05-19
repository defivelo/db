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

from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic.dates import MonthArchiveView
from django.views.generic.edit import UpdateView

from rolepermissions.mixins import HasPermissionsMixin

from defivelo.roles import user_cantons
from defivelo.views import MenuView

from .. import timesheets_overview
from ..forms import MonthlyCantonalValidationForm
from ..models import MonthlyCantonalValidation, MonthlyCantonalValidationUrl


class ValidationsMixin(HasPermissionsMixin, MenuView):
    model = MonthlyCantonalValidation
    required_permission = "cantons_mine"
    context_object_name = "mcvs"
    date_field = "date"

    def dispatch(self, request, *args, **kwargs):
        self.year = int(kwargs.pop("year"))
        self.month = int(kwargs.pop("month"))
        try:
            self.managed_cantons = user_cantons(request.user)
        except LookupError:
            self.managed_cantons = []
        self.canton = kwargs.get("canton", None)
        if self.canton and self.canton not in self.managed_cantons:
            # Vue individuelle, mais pas dans nos cantons
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Get the list of validations
        … but also make sure all the validations exist for that month and my cantons
        """
        return (
            super()
            .get_queryset()
            .filter(
                date__year=self.year,
                date__month=self.month,
                canton__in=self.managed_cantons,
            )
            .order_by("canton")
        ).prefetch_related("validated_urls")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] = "finance"
        context[
            "mcv_urls"
        ] = MonthlyCantonalValidationUrl.objects.all().prefetch_related("translations")
        return context


class ValidationsMonthView(ValidationsMixin, MonthArchiveView):
    allow_future = True
    allow_empty = True

    @cached_property
    def existing_cantons(self):
        return super().get_queryset().values_list("canton", flat=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible_users = timesheets_overview.get_visible_users(self.request.user)
        context[
            "timesheets_validation_status"
        ] = timesheets_overview.timesheets_validation_status(
            year=self.year,
            month=self.month,
            users=visible_users,
            cantons=([self.canton] if self.canton else self.managed_cantons),
        )
        context["nothing_to_do"] = all(
            [
                status is None
                for canton, status in context["timesheets_validation_status"].items()
            ]
        )
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        missing_cantons = [
            c for c in self.managed_cantons if c not in self.existing_cantons
        ]
        # Create the MCVs for the cantons' we're about to see (if needed)
        MonthlyCantonalValidation.objects.bulk_create(
            [
                MonthlyCantonalValidation(canton=c, date=date(self.year, self.month, 1))
                for c in missing_cantons
            ]
        )
        # Return the qs, that'll get the newly created ones.
        return qs


class ValidationUpdate(ValidationsMixin, UpdateView):
    context_object_name = "mcv"
    success_message = _("Validation cantonale mise à jour")
    form_class = MonthlyCantonalValidationForm

    def get_form_kwargs(self):
        fk = super().get_form_kwargs()
        fk["validator"] = self.request.user
        fk["urls"] = MonthlyCantonalValidationUrl.objects.all()
        visible_users = timesheets_overview.get_visible_users(self.request.user)
        fk[
            "timesheets_validation_status"
        ] = timesheets_overview.timesheets_validation_status(
            year=self.year,
            month=self.month,
            users=visible_users,
            cantons=[self.canton],
        )[
            self.canton
        ]
        return fk

    def get_initial(self):
        initial = super().get_initial()
        initial["validated"] = self.get_object().validated
        return initial

    def get_object(self, queryset=None):
        """
        Extrait l'objet à partir de l'URL plutôt que du pk
        Permet toujours une mise à jour; en créant l'objet si nécessaire
        """
        p, _ = (
            super()
            .get_queryset()
            .get_or_create(
                canton=self.canton, defaults={"date": date(self.year, self.month, 1)}
            )
        )
        return p

    def get_success_url(self):
        return reverse_lazy(
            "salary:validations-month",
            kwargs={"year": self.object.date.year, "month": self.object.date.month},
        )
