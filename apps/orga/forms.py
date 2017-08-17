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

from django import forms
from django.utils.translation import ugettext_lazy as _
from localflavor.ch.forms import CHPhoneNumberField, CHStateSelect, CHZipCodeField

from apps.user import STATE_CHOICES_WITH_DEFAULT

from . import ORGA_FIELDS
from .models import Organization


class OrganizationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        cantons = kwargs.pop('cantons', None)
        super(OrganizationForm, self).__init__(**kwargs)
        if cantons:
            # Only permit edition within the allowed cantons
            choices = self.fields['address_canton'].choices
            choices = (
                (k, v) for (k, v)
                in choices
                if k in cantons
            )
            self.fields['address_canton'].choices = choices

    address_canton = forms.ChoiceField(label=_('Canton'),
                                       widget=CHStateSelect,
                                       choices=STATE_CHOICES_WITH_DEFAULT,
                                       required=False)
    address_zip = CHZipCodeField(label=_('NPA'), max_length=4, required=False)
    coordinator_phone = CHPhoneNumberField(label=_('Téléphone'), required=False)
    coordinator_natel = CHPhoneNumberField(label=_('Natel'), required=False)

    class Meta:
        model = Organization
        fields = ORGA_FIELDS
