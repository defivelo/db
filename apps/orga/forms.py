# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from bootstrap3_datetime.widgets import DateTimePicker
from localflavor.ch.ch_states import STATE_CHOICES
from localflavor.ch.forms import CHStateSelect

from .models import Organization


class OrganizationForm(forms.ModelForm):
    address_canton = forms.ChoiceField(label=_('Canton'),
                                       widget=CHStateSelect,
                                       choices=tuple(
                                           list((('', _('Canton'),),)) +
                                           list(STATE_CHOICES)),
                                       required=False)

    class Meta:
        model = Organization
        fields = ['name', 'address_street', 'address_no', 'address_zip',
                  'address_city', 'address_canton']
