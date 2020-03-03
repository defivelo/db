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

from apps.challenge.models import Session

from .models import Invoice, InvoiceLine


class InvoiceForm(forms.ModelForm):
    sessions = forms.ModelMultipleChoiceField(queryset=Session.objects.all())

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

        # Circumvent weird bug due to the 'season' object being weird
        self.fields["season"].to_python = lambda x: x

    @transaction.atomic
    def save(self, commit=True):
        season = self.cleaned_data["season"]
        for refid in range(100, 999):
            ref = f"DV{season.year % 100}{refid:03d}"
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
        creating = not self.instance.pk
        invoice = super().save(commit=commit)

        if creating:
            # So we're in create.
            for session in self.cleaned_data["sessions"]:
                InvoiceLine.objects.create(
                    session=session,
                    invoice=invoice,
                    nb_participants=session.n_participants,
                    nb_bikes=session.n_bikes,
                    # TODO: replace by site cantonal setting
                    cost_bikes=(session.n_bikes * 9),
                    # TODO: replace by site cantonal setting
                    cost_participants=(session.n_participants * 4),
                )
        return invoice
