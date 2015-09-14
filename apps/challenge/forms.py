# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import autocomplete_light
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from bootstrap3_datetime.widgets import DateTimePicker
from localflavor.ch.forms import CHPhoneNumberField

from .models import MAX_MONO1_PER_QUALI, Qualification, Session


class SessionForm(autocomplete_light.ModelForm):
    day = forms.DateField(
        label=_('Date'),
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))

    class Meta:
        model = Session
        labels = {
            'begin': _('Horaire'),
            'organization': _('Établissement'),
        }
        fields = ['organization', 'day', 'begin', 'fallback_plan',
                  'address_street', 'address_no', 'address_zip',
                  'address_city', 'address_canton',
                  'apples',
                  'helpers_time', 'helpers_place',
                  'comments']


class QualificationForm(autocomplete_light.ModelForm):
    class_teacher_natel = CHPhoneNumberField(label=_('Natel enseignant'),
                                             required=False)

    def clean(self):
        # Check that we don't have too many moniteurs 1
        helpers = self.cleaned_data.get('helpers')
        if helpers and helpers.count() > MAX_MONO1_PER_QUALI:
            raise ValidationError(_('Pas plus de %s moniteurs 1 !') % MAX_MONO1_PER_QUALI)

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
            raise ValidationError(_('Il y a des moniteurs à double !'),
                                  code='double-helpers'
                                  )

        # Check that the picked actor corresponds to the activity_C
        actor = self.cleaned_data.get('actor')
        activity_C = self.cleaned_data.get('activity_C')
        if actor and activity_C:
            if actor.profile.actor_for != activity_C:
                raise ValidationError(
                    _("L'intervenant n'est pas qualifié pour la rencontre "
                        "prévue !"),
                    code='unqualified-actor')

        # Check that there are <= helmets or bikes than participants
        n_participants = self.cleaned_data.get('n_participants', 0)
        n_bikes = self.cleaned_data.get('n_bikes')
        if n_bikes and int(n_bikes) > int(n_participants):
            raise ValidationError(
                _("Il y a trop de vélos prévus !"),
                code='too-many-bikes')
        n_helmets = self.cleaned_data.get('n_helmets')
        if n_helmets and int(n_helmets) > int(n_participants):
            raise ValidationError(
                _("Il y a trop de casques prévus !"),
                code='too-many-helmets')

        return self.cleaned_data

    class Meta:
        model = Qualification
        widgets = {
            'session': forms.HiddenInput
        }
        fields = ['session', 'name',
                  'class_teacher_fullname', 'class_teacher_natel',
                  'n_participants', 'n_bikes', 'n_helmets',
                  'leader', 'helpers',
                  'activity_A', 'activity_B', 'activity_C', 'actor', 'route',
                  'comments']
        autocomplete_names = {'leader': 'Leaders',
                              'helpers': 'Helpers',
                              'actor': 'Actors'}
