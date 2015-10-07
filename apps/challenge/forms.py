# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import autocomplete_light
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from bootstrap3_datetime.widgets import DateTimePicker
from localflavor.ch.forms import CHPhoneNumberField

from .models import Qualification, Season, Session
from .models.availability import HelperSessionAvailability
from .models.qualification import MAX_MONO1_PER_QUALI


class SeasonForm(autocomplete_light.ModelForm):
    begin = forms.DateField(
        label=_('Début'),
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))
    end = forms.DateField(
        label=_('Fin'),
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))

    class Meta:
        model = Season
        fields = ['begin', 'end', 'cantons', 'leader']
        autocomplete_names = {'leader': 'AllPersons'}


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


class LeaderChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name()


class HelpersChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return (
            obj.get_full_name() +
            ' (%s)' % obj.profile.formation if obj.profile.formation != 'M1' else ''
        )


class QualificationForm(forms.ModelForm):
    class_teacher_natel = CHPhoneNumberField(label=_('Natel enseignant'),
                                             required=False)

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session')
        super(QualificationForm, self).__init__(*args, **kwargs)

        available_helpers = get_user_model().objects.filter(
            availabilities__chosen=True,
            availabilities__session=session
        )
        self.fields['leader'] = LeaderChoiceField(
            label=_('Moniteur 2'),
            queryset=available_helpers.filter(profile__formation='M2')
        )
        self.fields['helpers'] = HelpersChoiceField(
            label=_('Moniteurs 1'),
            queryset=available_helpers.filter(
                profile__formation__in=['M1', 'M2']
            )
        )

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


class BSRadioRenderer(forms.widgets.RadioFieldRenderer):
    def render(self):
        id_ = self.attrs.get('id', None)
        options = ''
        try:
            optionvalue = self.value[0]
        except IndexError:
            optionvalue = ''
        try:
            chosen = (self.value[1] == '*')
        except IndexError:
            chosen = False
        for option in self.choices:
            level = 'danger'
            glyphicon = 'remove-circle'
            if option[0] == 'y':
                level = 'success'
                glyphicon = 'ok-sign'
            elif option[0] == 'i':
                level = 'warning'
                glyphicon = 'ok-circle'
            checked = 'checked' if optionvalue == option[0] else ''
            active = 'active' if optionvalue == option[0] else ''
            disabled = 'disabled' if (option[0] == 'n' and chosen) else ''
            options += (
                '<label title="{label}"'
                '       class="btn btn-{level} {active} {disabled}">'
                '  <input type="radio" autocomplete="off"'
                '         name="{key}" id="{key}-{value}" value="{value}"'
                '         {checked} {disabled}>'
                '    <span class="glyphicon glyphicon-{glyphicon}"'
                '          title="{label}"></span> '
                '</label>\n').format(
                    level=level,
                    glyphicon=glyphicon,
                    key=id_,
                    value=option[0],
                    label=(
                        option[1] if not disabled
                        else _('Sélectionné pour une quali, impossible')
                    ),
                    checked=checked,
                    active=active,
                    disabled=disabled)
        return (
            '<div class="btn-group-vertical" data-toggle="buttons">'
            '{options}</div>').format(options=options)


class BSCheckBoxRenderer(forms.widgets.CheckboxFieldRenderer):
    def render(self):
        id_ = self.attrs.get('id', None)
        checked = 'checked' if self.value else ''
        active = 'active' if self.value else ''
        checkbox = (
            '<label title="{label}"'
            '       class="btn btn-{level} {active}">'
            '  <input type="checkbox" autocomplete="off" '
            '         name="{key}" id="{key}-{value}" value="{value}" {checked}>'
            '    <span class="glyphicon glyphicon-{glyphicon}"'
            '          title="{label}"></span> '
            '</label>\n').format(
                level='primary',
                glyphicon='user',
                key=id_,
                value=1,
                label=_('Choisir pour cette session'),
                checked=checked,
                active=active)
        return (
            '<div data-toggle="buttons">'
            '{checkbox}</div>').format(checkbox=checkbox)


class SeasonNewHelperAvailabilityForm(forms.Form):
    helper = autocomplete_light.ChoiceField('PersonsRelevantForSessions',
                                            label=_('Disponibilités pour:'))


class SeasonAvailabilityForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.season = kwargs.pop('instance')
        self.potential_helpers = kwargs.pop('potential_helpers')
        super(SeasonAvailabilityForm, self).__init__(*args, **kwargs)

        if self.potential_helpers:
            for helper_category, helpers in self.potential_helpers:
                for helper in helpers:
                    for session in self.season.sessions_with_qualifs:
                        availkey = 'avail-h{hpk}-s{spk}'.format(hpk=helper.pk,
                                                                spk=session.pk)
                        staffkey = 'staff-h{hpk}-s{spk}'.format(hpk=helper.pk,
                                                                spk=session.pk)
                        try:
                            fieldinit = self.initial[availkey]
                        except:
                            pass
                        # Trick to pass the 'chosen' information through
                        try:
                            fieldinit += '*' if self.initial[staffkey] else ''
                        except:
                            pass

                        self.fields[availkey] = forms.ChoiceField(
                            choices=HelperSessionAvailability.AVAILABILITY_CHOICES,
                            widget=forms.RadioSelect(renderer=BSRadioRenderer),
                            required=False, initial=fieldinit
                        )

    def save(self):
        pass


class SeasonStaffChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.season = kwargs.pop('instance')
        self.available_helpers = kwargs.pop('available_helpers')
        super(SeasonStaffChoiceForm, self).__init__(*args, **kwargs)

        if self.available_helpers:
            for helper_category, helpers in self.available_helpers:
                for helper in helpers:
                    for session in self.season.sessions_with_qualifs:
                        availkey = 'avail-h{hpk}-s{spk}'.format(hpk=helper.pk,
                                                                spk=session.pk)
                        staffkey = 'staff-h{hpk}-s{spk}'.format(hpk=helper.pk,
                                                                spk=session.pk)
                        ## If the availability is not 'y' or 'i', skip that one
                        #if self.initial[availkey] not in ['i', 'y']:
                            #continue
                        try:
                            fieldinit = self.initial[staffkey]
                        except:
                            pass
                        self.fields[staffkey] = forms.BooleanField(
                            widget=forms.RadioSelect(renderer=BSCheckBoxRenderer),
                            required=False, initial=fieldinit
                        )

    def save(self):
        pass
