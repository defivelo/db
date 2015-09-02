# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import autocomplete_light
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from bootstrap3_datetime.widgets import DateTimePicker

from .models import Qualification, Session


class SessionForm(autocomplete_light.ModelForm):
    day = forms.DateField(
        label=_('Date'),
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))

    class Meta:
        model = Session
        labels = {
            'timeslot': _('Horaire'),
            'organization': _('Établissement'),
        }
        fields = ['organization', 'day', 'timeslot']


class QualificationForm(autocomplete_light.ModelForm):
    def clean(self):
        # Check that we don't have too many moniteurs 1
        helpers = self.cleaned_data.get('helpers')
        if helpers and helpers.count() > 2:
            raise ValidationError(_('Pas plus de %s moniteurs 1 !') % 2)

        # Check that all moniteurs are unique
        all_leaders_pk = []
        leader = self.cleaned_data.get('leader')
        if leader:
            all_leaders_pk.append(leader.pk)
        if helpers:
            for helper in helpers.all():
                all_leaders_pk.append(helper.pk)
        # Check unicity
        seen_pk = set()
        if len([x for x in all_leaders_pk if x not in seen_pk and not seen_pk.add(x)]) < len(all_leaders_pk):
            raise ValidationError(_('Il y a des moniteurs à double !'))
        return self.cleaned_data

    class Meta:
        model = Qualification
        widgets = {
            'session': forms.HiddenInput
        }
        fields = ['session', 'name',
                  'leader', 'helpers',
                  'activity_A', 'activity_B', 'activity_C']
        autocomplete_names = {'leader': 'Leaders',
                              'helpers': 'Helpers'}
