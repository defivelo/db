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
from autocomplete_light import AutocompleteModelBase, register as al_register
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.html import escape

from apps.challenge import MAX_MONO1_PER_QUALI

from .models import FORMATION_KEYS, FORMATION_M2


class PersonAutocomplete(AutocompleteModelBase):
    search_fields = ['first_name', 'last_name']
    model = settings.AUTH_USER_MODEL

    def choice_label(self, choice):
        return choice.get_full_name()

    def choice_html(self, choice):
        """
        Override autocomplete_light to drop the 'escape' call over choice_label
        """
        return self.choice_html_format % (
            escape(self.choice_value(choice)),
            self.choice_label(choice))

al_register(PersonAutocomplete, name='AllPersons',
            choices=get_user_model().objects.all(),
            widget_attrs={
                'data-widget-maximum-values': 1,
            })

al_register(PersonAutocomplete, name='PersonsRelevantForSessions',
            choices=get_user_model().objects.filter(
                Q(profile__formation__in=FORMATION_KEYS) |
                Q(profile__actor_for__isnull=False) |
                Q(profile__office_member=True)
            ),
            widget_attrs={
                'data-widget-maximum-values': 1,
            })


class HelpersAutocomplete(PersonAutocomplete):
    def choice_label(self, choice):
        return "{name} {icon}".format(
            name=choice.get_full_name(),
            icon=choice.profile.formation_icon())

al_register(HelpersAutocomplete, name='Helpers',
            choices=get_user_model().objects.filter(
                Q(profile__formation__in=FORMATION_KEYS) |
                Q(profile__office_member=True)
                ),
            widget_attrs={
                'data-widget-maximum-values': MAX_MONO1_PER_QUALI,
            })
al_register(HelpersAutocomplete, name='Leaders',
            choices=get_user_model().objects.filter(
                Q(profile__formation=FORMATION_M2) |
                Q(profile__office_member=True)
                )
            )


class ActorsAutocomplete(PersonAutocomplete):
    def choice_label(self, choice):
        return "{name} ({actor_for})".format(
            name=choice.get_full_name(),
            actor_for=choice.profile.actor_for.name)


al_register(ActorsAutocomplete, name='Actors',
            choices=get_user_model().objects.exclude(profile__actor_for__isnull=True))
