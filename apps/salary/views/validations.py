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
from django.db import transaction
from django.urls import reverse_lazy
from django.utils.dates import MONTHS_3
from django.utils.translation import ugettext_lazy as _
from django.views.generic.dates import MonthArchiveView, YearArchiveView
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
        try:
            self.month = int(kwargs.pop("month"))
        except KeyError:
            self.month = None
        try:
            self.managed_cantons = user_cantons(request.user)
            self.managed_cantons.sort()
        except LookupError:
            self.managed_cantons = []
        self.canton = kwargs.get("canton", None)
        if self.canton and self.canton not in self.managed_cantons:
            # Vue individuelle, mais pas dans nos cantons
            raise PermissionDenied
        self.timesheets_statuses = timesheets_overview.timesheets_validation_status(
            year=self.year,
            month=self.month,
            cantons=([self.canton] if self.canton else self.managed_cantons),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Get the list of validations
        … but also make sure all the validations exist for that month and my cantons
        """
        kwargs = {"date__year": self.year, "canton__in": self.managed_cantons}
        if self.month:
            kwargs["date__month"] = self.month
        return (
            super().get_queryset().filter(**kwargs).order_by("canton", "date")
        ).prefetch_related("validated_urls")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] = "finance"
        context["timesheets_statuses"] = self.timesheets_statuses
        context[
            "mcv_urls"
        ] = MonthlyCantonalValidationUrl.objects.all().prefetch_related("translations")
        return context

    def queryset_all_mcvs_in_month(self, queryset, year, month):
        """
        Using a given queryset, make sure that for a given year/month, all "my" cantons
        have created MonthlyCantonalValidation objects
        """
        # At this point, make extra sure we have all the needed ones
        with transaction.atomic():
            existing_cantons = list(
                MonthlyCantonalValidation.objects.filter(
                    date__year=year, date__month=month
                ).values_list("canton", flat=True)
            )
            missing_objects = [
                MonthlyCantonalValidation(canton=c, date=date(year, month, 1))
                for c in self.managed_cantons
                if c not in existing_cantons
            ]
            # Create the MCVs for the cantons' we're about to see (if needed)
            MonthlyCantonalValidation.objects.bulk_create(
                missing_objects, ignore_conflicts=True
            )
        return queryset.filter(canton__in=self.managed_cantons, date__year=year)


class ValidationsYearView(ValidationsMixin, YearArchiveView):
    allow_future = True
    allow_empty = True
    make_object_list = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Swap the array to get a canton: dict entry with 12 entries
        context["timesheets_statuses_by_canton"] = {}
        for canton in self.managed_cantons:
            context["timesheets_statuses_by_canton"][canton] = {}
            for m in MONTHS_3.keys():
                context["timesheets_statuses_by_canton"][canton][m] = context[
                    "timesheets_statuses"
                ][m].get(canton, None)
        context["months"] = MONTHS_3
        return context

    def get_queryset(self):
        """
        Make sure all the MonthlyCantonalValidation objects exist in this year, so in all months
        """
        qs = super().get_queryset()
        for month in MONTHS_3.keys():
            qs = self.queryset_all_mcvs_in_month(qs, self.year, month)
        # Return the qs, that'll get the newly created ones.
        return qs


class ValidationsMonthView(ValidationsMixin, MonthArchiveView):
    allow_future = True
    allow_empty = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nothing_to_do"] = all(
            [status is None for _, status in context["timesheets_statuses"].items()]
        )
        return context

    def get_queryset(self):
        """
        Make sure all the MonthlyCantonalValidation objects exist in this month
        """
        return self.queryset_all_mcvs_in_month(
            super().get_queryset(), self.year, self.month
        )


class ValidationUpdate(ValidationsMixin, UpdateView):
    context_object_name = "mcv"
    success_message = _("Validation cantonale mise à jour")
    form_class = MonthlyCantonalValidationForm

    def get_form_kwargs(self):
        fk = super().get_form_kwargs()
        fk["validator"] = self.request.user
        fk["urls"] = MonthlyCantonalValidationUrl.objects.all()
        fk["timesheets_statuses"] = self.timesheets_statuses
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
