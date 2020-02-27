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
from django.db import transaction

from apps.challenge.models import Session

from .models import Invoice, InvoiceLine


class CreateInvoiceForm(forms.ModelForm):
    sessions = forms.ModelMultipleChoiceField(queryset=Session.objects.none())

    class Meta:
        model = Invoice
        fields = [
            "title",
            "organization",
            "season",
        ]

    def __init__(self, organization, season, *args, **kwargs):
        self.organization = organization
        self.season = season

        super().__init__(*args, **kwargs)

        self.fields["sessions"].queryset = season.sessions.filter(orga=organization)

    @transaction.atomic
    def save(self, commit=True):
        invoice = super().save(commit=commit)

        for session in self.cleaned_data["sessions"]:
            InvoiceLine.objects.create(
                session=session,
                invoice=invoice,
                nb_participants=session.n_participants,
                nb_bikes=session.n_bikes,
            )
