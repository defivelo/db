from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.forms import IBANFormField


class UserProfileForm(forms.ModelForm):
    iban = IBANFormField(label=_('Coordonnées bancaires (IBAN)'), include_countries=IBAN_SEPA_COUNTRIES, required=False)
    
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'iban' ]
