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
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from localflavor.ch.forms import CHPhoneNumberField, CHSocialSecurityNumberField, CHStateSelect, CHZipCodeField
from localflavor.generic import forms as localforms
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from multiselectfield.forms.fields import MultiSelectFormField

from apps.challenge.models import QualificationActivity
from apps.common import DV_LANGUAGES, DV_LANGUAGES_WITH_DEFAULT, DV_STATE_CHOICES, DV_STATE_CHOICES_WITH_DEFAULT
from apps.common.forms import BS3CountriesField, SwissDateField

from . import STATE_CHOICES_WITH_DEFAULT
from .models import BAGSTATUS_CHOICES, FORMATION_CHOICES, USERSTATUS_CHOICES_NORMAL


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        allow_email = kwargs.pop('allow_email', False)
        # Whether to permit no-affiliation-canton creation
        affiliation_canton_required = kwargs.pop('affiliation_canton_required', True)
        cantons = kwargs.pop('cantons', None)
        super(UserProfileForm, self).__init__(*args, **kwargs)

        if not allow_email and 'email' in self.fields:
            del(self.fields['email'])
        for field in 'first_name', 'last_name', 'email':
            if field in self.fields:
                self.fields[field].required = True

        if cantons:
            # Only permit edition within the allowed cantons
            choices = self.fields['affiliation_canton'].choices
            choices = (
                (k, v) for (k, v)
                in choices
                if k in cantons or (not affiliation_canton_required and k == '')
            )
            self.fields['affiliation_canton'].required = affiliation_canton_required
            self.fields['affiliation_canton'].choices = choices

    language = forms.ChoiceField(label=_('Langue'), choices=DV_LANGUAGES_WITH_DEFAULT,
                                 required=False)
    languages_challenges = MultiSelectFormField(
        label=_('Prêt à animer en'), choices=DV_LANGUAGES,
        required=False)
    address_street = forms.CharField(label=_('Rue'), max_length=255,
                                     required=False)
    address_no = forms.CharField(label=_('N°'), max_length=8,
                                 required=False)
    address_zip = CHZipCodeField(label=_('NPA'), max_length=4, required=False)
    address_city = forms.CharField(label=_('Ville'), max_length=64,
                                   required=False)
    address_canton = forms.ChoiceField(label=_('Canton'),
                                       widget=CHStateSelect,
                                       choices=STATE_CHOICES_WITH_DEFAULT,
                                       required=False)
    birthdate = SwissDateField(label=_('Date de naissance'), required=False)
    natel = CHPhoneNumberField(label=_('Natel'), required=False)
    nationality = BS3CountriesField(label=_('Nationalité'))
    work_permit = forms.CharField(label=_('Permis de travail'),
                                  widget=forms.TextInput(
                                      attrs={'placeholder': ('… si pas Suisse')}
                                  ),
                                  max_length=255, required=False)
    iban = localforms.IBANFormField(label=_('Coordonnées bancaires (IBAN)'),
                                    include_countries=IBAN_SEPA_COUNTRIES,
                                    required=False)
    social_security = CHSocialSecurityNumberField(label=_('N° AVS'),
                                                  max_length=16,
                                                  required=False)
    formation = forms.ChoiceField(label=_('Formation'),
                                  choices=FORMATION_CHOICES,
                                  required=False)
    formation_lastdate = SwissDateField(
        label=_('Date de la dernière formation'), required=False)
    actor_for = forms.ModelChoiceField(label=_('Intervenant'),
                                       queryset=(
                                           QualificationActivity.objects
                                           .filter(category='C')
                                       ),
                                       required=False)
    status = forms.ChoiceField(label=_('Statut'),
                               choices=USERSTATUS_CHOICES_NORMAL,
                               required=False)
    pedagogical_experience = forms.CharField(label=_('Expérience pédagogique'),
                                             required=False)
    firstmed_course = forms.BooleanField(label=_('Cours samaritain suivi'),
                                         required=False)
    firstmed_course_comm = forms.CharField(label=_('Cours samaritain suivi?'),
                                           required=False)
    bagstatus = forms.ChoiceField(label=_('Sac Défi Vélo'),
                                  choices=BAGSTATUS_CHOICES,
                                  required=False)
    comments = forms.CharField(label=_('Remarques'), widget=forms.Textarea,
                               required=False
                               )
    affiliation_canton = forms.ChoiceField(
        label=_("Canton d'affiliation"),
        choices=DV_STATE_CHOICES_WITH_DEFAULT,
        required=False)
    activity_cantons = MultiSelectFormField(label=_("Défi Vélo Mobile"),
                                            choices=DV_STATE_CHOICES,
                                            required=False)

    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email', ]
