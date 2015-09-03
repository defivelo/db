# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from localflavor.ch.ch_states import STATE_CHOICES
from localflavor.ch.forms import (
    CHPhoneNumberField, CHSocialSecurityNumberField, CHStateSelect,
    CHZipCodeField,
)
from localflavor.generic import forms as localforms
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES

from apps.challenge.models import QualificationActivity

from .models import FORMATION_CHOICES


class UserProfileForm(forms.ModelForm):
    address_street = forms.CharField(label=_('Rue'), max_length=255,
                                     required=False)
    address_no = forms.CharField(label=_('N°'), max_length=8,
                                 required=False)
    address_zip = CHZipCodeField(label=_('NPA'), max_length=4, required=False)
    address_city = forms.CharField(label=_('Ville'), max_length=64,
                                   required=False)
    address_canton = forms.ChoiceField(label=_('Canton'),
                                       widget=CHStateSelect,
                                       choices=tuple(
                                           list((('', _('Canton'),),)) +
                                           list(STATE_CHOICES)),
                                       required=False)
    natel = CHPhoneNumberField(label=_('Natel'), required=False)
    iban = localforms.IBANFormField(label=_('Coordonnées bancaires (IBAN)'),
                                    include_countries=IBAN_SEPA_COUNTRIES,
                                    required=False)
    social_security = CHSocialSecurityNumberField(label=_('N° AVS'),
                                                  max_length=16,
                                                  required=False)
    formation = forms.ChoiceField(label=_('Formation'),
                                  choices=FORMATION_CHOICES,
                                  required=False)
    actor_for = forms.ModelChoiceField(label=_('Intervenant'),
                                       queryset=QualificationActivity.objects.filter(category='C'),
                                       required=False)

    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email']
