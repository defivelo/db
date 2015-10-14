# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from apps.user import STATE_CHOICES_WITH_DEFAULT
from bootstrap3_datetime.widgets import DateTimePicker
from localflavor.ch.forms import CHStateSelect

from .models import Organization


class OrganizationForm(forms.ModelForm):
    address_canton = forms.ChoiceField(label=_('Canton'),
                                       widget=CHStateSelect,
                                       choices=STATE_CHOICES_WITH_DEFAULT,
                                       required=False)

    class Meta:
        model = Organization
        fields = ['name', 'address_street', 'address_no', 'address_additional',
                  'address_zip', 'address_city', 'address_canton']
