# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2020 Sylvain Fankhauser <sylvain.fankhauser@liip.ch>
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

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from apps.challenge.models import AnnualStateSetting, Season, Session

from ..models import Invoice, InvoiceLine


class InvoiceForm(forms.ModelForm):
    sessions = forms.ModelMultipleChoiceField(queryset=Session.objects.none())

    class Meta:
        model = Invoice
        fields = [
            "title",
            "status",
            "organization",
            "season",
        ]

    def __init__(self, organization, season, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sessions = season.sessions.filter(orga=organization)
        self.fields["sessions"].queryset = sessions
        self.fields["sessions"].initial = sessions

        for f in ["organization", "season", "sessions"]:
            self.fields[f].disabled = True

        #  Reduce the number of convoluted queries. We know we want this one only.
        self.fields["season"].queryset = Season.objects.filter(pk=season.pk)

        # Circumvent weird bug due to the 'season' object being weird
        self.fields["season"].to_python = lambda x: x

    @transaction.atomic
    def save(self, commit=True):
        creating = not self.instance.pk
        season = self.cleaned_data["season"]
        if creating:
            ref_prefix = f"DV{season.year % 100}"
            try:
                largestref = (
                    Invoice.objects.filter(ref__startswith=ref_prefix)
                    .order_by("-ref")
                    .first()
                    .ref
                )
                startrefid = int(largestref[len(ref_prefix) :]) + 1
            except (AttributeError, ValueError):
                startrefid = 100
            for refid in range(startrefid, 999):
                ref = f"{ref_prefix}{refid:03d}"
                self.instance.ref = ref

                if not Invoice.objects.filter(ref=ref).exists():
                    # If unicity is garanteed, proceed
                    break
            else:
                # This should not happen.
                raise ValidationError(
                    _(
                        f"L'espace des factures établissements pour l'année {season.year} est épuisé avec l'identifiant {ref}."
                    )
                )
        invoice = super().save(commit=commit)

        try:
            settings = AnnualStateSetting.objects.get(
                canton=invoice.organization.address_canton, year=season.year
            )
        except AnnualStateSetting.DoesNotExist:
            settings = AnnualStateSetting(cost_per_bike=0, cost_per_participant=0)

        if creating:
            for session in self.cleaned_data["sessions"]:
                InvoiceLine.objects.create(
                    session=session,
                    invoice=invoice,
                    nb_participants=session.n_participants,
                    nb_bikes=session.n_bikes,
                    cost_bikes=(session.n_bikes * settings.cost_per_bike),
                    cost_participants=(
                        session.n_participants * settings.cost_per_participant
                    ),
                )
        elif not invoice.is_locked:
            # We're in update, but still in draft mode
            for session in self.cleaned_data["sessions"]:
                InvoiceLine.objects.update_or_create(
                    session=session,
                    invoice=invoice,
                    defaults={
                        "nb_participants": session.n_participants,
                        "nb_bikes": session.n_bikes,
                        "cost_bikes": (session.n_bikes * settings.cost_per_bike),
                        "cost_participants": (
                            session.n_participants * settings.cost_per_participant
                        ),
                    },
                )
        return invoice
