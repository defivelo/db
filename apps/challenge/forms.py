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

from dal_select2.widgets import ModelSelect2
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.defaultfilters import date
from django.utils.translation import ugettext_lazy as _
from localflavor.ch.forms import CHPhoneNumberField, CHStateSelect

from apps.common.forms import SwissDateField, SwissTimeField, UserAutoComplete
from apps.user import STATE_CHOICES_WITH_DEFAULT
from apps.user.models import FORMATION_KEYS, FORMATION_M2

from . import (
    AVAILABILITY_FIELDKEY, MAX_MONO1_PER_QUALI, SHORTCODE_ACTOR, SHORTCODE_MON1, SHORTCODE_MON2, STAFF_FIELDKEY,
)
from .fields import ActorChoiceField, HelpersChoiceField, LeaderChoiceField
from .models import Qualification, Season, Session
from .models.availability import HelperSessionAvailability


class SeasonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        cantons = kwargs.pop('cantons', None)
        kwargs.pop('season', None)
        super(SeasonForm, self).__init__(**kwargs)
        if cantons:
            # Only permit edition within the allowed cantons
            choices = self.fields['cantons'].choices
            choices = (
                (k, v) for (k, v)
                in choices
                if k in cantons
            )
            self.fields['cantons'].choices = choices

    def clean_end(self):
        begin = self.cleaned_data.get("begin")
        end = self.cleaned_data.get("end")
        if end <= begin:
            raise forms.ValidationError(
                _("La fin doit être après le début.")
            )
        return end

    begin = SwissDateField(label=_('Début'))
    end = SwissDateField(label=_('Fin'))
    leader = LeaderChoiceField(label=_('Chargé·e de projet'),
                               queryset=(
                                   get_user_model().objects
                                   .filter(managedstates__isnull=False)
                                   .distinct()
                                ),
                               required=True)

    class Meta:
        model = Season
        fields = ['begin', 'end', 'cantons', 'leader']


class SessionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('cantons', None)
        self.season = kwargs.pop('season', None)
        super(SessionForm, self).__init__(**kwargs)
        if self.season.cantons:
            # Only permit orgas within the allowed cantons
            qs = (
                self.fields['orga'].queryset
                .filter(address_canton__in=self.season.cantons)
            )
            self.fields['orga'].queryset = qs
        try:
            self.fields['day'].widget.options['minDate'] = \
                self.season.begin.strftime('%Y-%m-%d')
            self.fields['day'].widget.options['maxDate'] = \
                self.season.end.strftime('%Y-%m-%d')
        except:
            pass

    day = SwissDateField(label=_('Date'))
    begin = SwissTimeField(label=_('Début'), required=False)
    address_canton = forms.ChoiceField(label=_('Canton'),
                                       widget=CHStateSelect,
                                       choices=STATE_CHOICES_WITH_DEFAULT,
                                       required=False)
    apples = forms.CharField(label=_('Pommes'),
                             required=False,
                             widget=forms.TextInput(
                                 {'placeholder': _(
                                     'Organisation de la livraison de pommes '
                                     '(quantité & logistique)'
                                     )}))
    helpers_time = SwissTimeField(label=_('Heure rendez-vous moniteurs'),
                                  required=False)
    superleader = UserAutoComplete(label=_('Moniteur +'),
                                   queryset=get_user_model().objects,
                                   url='user-AllPersons-ac')

    def clean_day(self):
        day = self.cleaned_data['day']
        if self.season.begin <= day <= self.season.end:
            return day
        raise forms.ValidationError(
            _('La session doit être dans la saison'
              ' (entre {begin} et {end})').format(
                  begin=date(self.season.begin, settings.DATE_FORMAT),
                  end=date(self.season.end, settings.DATE_FORMAT),
                  ))

    class Meta:
        model = Session
        labels = {
            'orga': _('Établissement'),
        }
        fields = ['orga', 'day', 'begin', 'fallback_plan',
                  'place',
                  'address_street', 'address_no', 'address_zip',
                  'address_city', 'address_canton',
                  'superleader',
                  'apples',
                  'helpers_time', 'helpers_place',
                  'comments']


class QualificationForm(forms.ModelForm):
    class_teacher_natel = CHPhoneNumberField(label=_('Natel enseignant'),
                                             required=False)

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session')
        kwargs.pop('season', None)
        kwargs.pop('cantons', None)
        super(QualificationForm, self).__init__(*args, **kwargs)
        other_qualifs = session.qualifications.exclude(pk=self.instance.pk)
        available_staff = (
            get_user_model().objects.filter(
                Q(
                    availabilities__chosen=True,
                    availabilities__session=session
                )
            )
            .exclude(
                Q(qualifs_mon2__in=other_qualifs) |
                Q(qualifs_mon1__in=other_qualifs) |
                Q(qualifs_actor__in=other_qualifs)
            )
            .distinct()
            .order_by('first_name')
        )
        self.fields['leader'] = LeaderChoiceField(
            label=_('Moniteur 2'),
            queryset=available_staff.filter(
                Q(profile__formation=FORMATION_M2)
            ),
            required=False,
        )
        self.fields['helpers'] = HelpersChoiceField(
            label=_('Moniteurs 1'),
            queryset=available_staff.filter(
                Q(profile__formation__in=FORMATION_KEYS)
            ),
            required=False,
        )
        self.fields['actor'] = ActorChoiceField(
            label=_('Intervenant'),
            queryset=available_staff.exclude(
                profile__actor_for__isnull=True
            ),
            required=False
        )

    def clean_helpers(self):
        # Check that we don't have too many moniteurs 1
        helpers = self.cleaned_data.get('helpers')
        if helpers and helpers.count() > MAX_MONO1_PER_QUALI:
            raise ValidationError(
                _('Pas plus de %s moniteurs 1 !') % MAX_MONO1_PER_QUALI
            )
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
        if len([
            x for x in all_leaders_pk
            if x not in seen_pk and not seen_pk.add(x)
        ]) < len(all_leaders_pk):
            raise ValidationError(_('Il y a des moniteurs à double !'),
                                  code='double-helpers'
                                  )
        return helpers

    def clean_actor(self):
        # Check that the picked actor corresponds to the activity_C
        actor = self.cleaned_data.get('actor')
        activity_C = self.cleaned_data.get('activity_C')
        if actor and activity_C:
            if actor.profile.actor_for != activity_C:
                raise ValidationError(
                    _("L'intervenant n'est pas qualifié pour la rencontre "
                        "prévue !"),
                    code='unqualified-actor')
        return actor

    def clean(self):
        # Check that there are <= helmets or bikes than participants
        n_participants = self.cleaned_data.get('n_participants')
        if not n_participants:
            n_participants = 0
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
                  'activity_A', 'activity_B', 'activity_C', 'actor',
                  'comments']


#class BSRadioRenderer(forms.widgets.ChoiceFieldRenderer):
    #def render(self):
        #id_ = self.attrs.get('id', None)
        #options = ''
        #try:
            #optionvalue = self.value[0]
        #except IndexError:
            #optionvalue = ''
        #try:
            #chosen = (self.value[1] == '*')
        #except IndexError:
            #chosen = False
        #for option in self.choices:
            #level = 'danger'
            #glyphicon = 'remove-circle'
            #if option[0] == 'y':
                #level = 'success'
                #glyphicon = 'ok-sign'
            #elif option[0] == 'i':
                #level = 'warning'
                #glyphicon = 'ok-circle'
            #checked = 'checked' if optionvalue == option[0] else ''
            #active = 'active' if optionvalue == option[0] else ''
            #disabled = 'disabled' if (option[0] == 'n' and chosen) else ''
            #options += (
                #'<label title="{label}"'
                #'       class="btn btn-default {active} {disabled}"'
                #'       data-active-class="{level}">'
                #'  <input type="radio" autocomplete="off"'
                #'         name="{key}" id="{key}-{value}" value="{value}"'
                #'         {checked} {disabled}>'
                #'    <span class="glyphicon glyphicon-{glyphicon}"'
                #'          title="{label}"></span> '
                #'</label>\n').format(
                    #level=level,
                    #glyphicon=glyphicon,
                    #key=id_,
                    #value=option[0],
                    #label=(
                        #option[1] if not disabled
                        #else _('Sélectionné pour une quali, impossible')
                    #),
                    #checked=checked,
                    #active=active,
                    #disabled=disabled)
        #return (
            #'<div class="btn-group-vertical" data-toggle="buttons">'
            #'{options}</div>').format(options=options)


#class BSCheckBoxRenderer(forms.widgets.CheckboxFieldRenderer):
    #def render(self):
        #id_ = self.attrs.get('id', None)
        #chosen_as = False
        #try:
            #value = (self.value[0] == 'Y')
            #try:
                #chosen_as = self.value[1]
            #except IndexError:
                #pass
        #except IndexError:
            #value = False

        #checked = 'checked' if value else ''
        #active = 'active' if value else ''

        #glyphicon = 'check'
        #title = _('Choisir pour cette session')
        #if chosen_as == SHORTCODE_MON2:  # Moniteur 2
            #glyphicon = 'tags'
            #title = _('Moniteur 2')
        #if chosen_as == SHORTCODE_MON1:  # Moniteur 1
            #glyphicon = 'tag'
            #title = _('Moniteur 1')
        #if chosen_as == SHORTCODE_ACTOR:  # Intervenant
            #glyphicon = 'sunglasses'
            #title = _('Intervenant')

        #checkbox = (
            #'<label title="{label}"'
            #'       class="btn btn-default {active}"'
            #'       data-active-class="primary">'
            #'  <input type="checkbox" autocomplete="off" '
            #'         name="{key}" id="{key}-{value}" value="{value}"'
            #'         {checked}>'
            #'    <span class="glyphicon glyphicon-unchecked"'
            #'          data-active-icon="{glyphicon}"'
            #'          title="{label}"></span> '
            #'</label>\n').format(
                #glyphicon=glyphicon,
                #key=id_,
                #value=1,
                #label=title,
                #checked=checked,
                #active=active)
        #return (
            #'<div data-toggle="buttons">'
            #'{checkbox}</div>').format(checkbox=checkbox)


class SeasonNewHelperAvailabilityForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SeasonNewHelperAvailabilityForm, self).__init__(*args, **kwargs)
        self.fields['helper'] = \
            forms.ModelChoiceField(
                label=_('Disponibilités pour :'),
                queryset=get_user_model().objects.filter(
                    Q(profile__formation__in=FORMATION_KEYS) |
                    Q(profile__actor_for__isnull=False)
                ),
                widget=ModelSelect2(url='user-PersonsRelevantForSessions-ac')
            )


class SeasonAvailabilityForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.season = kwargs.pop('instance')
        self.potential_helpers = kwargs.pop('potential_helpers')
        kwargs.pop('season', None)
        kwargs.pop('cantons', None)
        super(SeasonAvailabilityForm, self).__init__(*args, **kwargs)

        if self.potential_helpers:
            for helper_category, helpers in self.potential_helpers:
                for helper in helpers:
                    for session in self.season.sessions_with_qualifs:
                        availkey = AVAILABILITY_FIELDKEY.format(hpk=helper.pk,
                                                                spk=session.pk)
                        staffkey = STAFF_FIELDKEY.format(hpk=helper.pk,
                                                         spk=session.pk)
                        try:
                            fieldinit = self.initial[availkey]
                        except:
                            fieldinit = ''
                        # Trick to pass the 'chosen' information through
                        try:
                            fieldinit += '*' if self.initial[staffkey] else ''
                        except:
                            pass

                        self.fields[availkey] = forms.ChoiceField(
                            choices=HelperSessionAvailability.AVAILABILITY_CHOICES,  # NOQA
                            widget=forms.RadioSelect(),
                            required=False, initial=fieldinit
                        )

    def save(self):
        pass


class SeasonStaffChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.season = kwargs.pop('instance')
        self.available_helpers = kwargs.pop('available_helpers')
        kwargs.pop('season', None)
        kwargs.pop('cantons', None)
        super(SeasonStaffChoiceForm, self).__init__(*args, **kwargs)

        if self.available_helpers:
            for helper_category, helpers in self.available_helpers:
                for helper in helpers:
                    for session in self.season.sessions_with_qualifs:
                        AVAILABILITY_FIELDKEY.format(
                            hpk=helper.pk, spk=session.pk)
                        staffkey = STAFF_FIELDKEY.format(hpk=helper.pk,
                                                         spk=session.pk)
                        # Stupid boolean to integer-as-string conversion.
                        try:
                            fieldinit = 'Y' if self.initial[staffkey] else 'N'
                        except KeyError:
                            fieldinit = 'N'
                        # Trick to pass the 'at which role that user is
                        # selected in that quali' information through
                        fieldinit += session.user_assignment(helper)

                        self.fields[staffkey] = forms.BooleanField(
                            widget=forms.RadioSelect(),
                            required=False, initial=fieldinit
                        )

    def save(self):
        pass
