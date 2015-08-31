# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import autocomplete_light

from django import forms
from django.utils.translation import ugettext_lazy as _

from bootstrap3_datetime.widgets import DateTimePicker

from .models import Session


class SessionForm(autocomplete_light.ModelForm):
    day = forms.DateField(label=_('Date'),
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))

    class Meta:
        model = Session
        labels = {
            'timeslot': _('Horaire'),
            'organization': _('Établissement'),
        }
        fields = ['organization', 'day', 'timeslot',]
