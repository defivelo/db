# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015, 2016 Didier Raboud <me+defivelo@odyx.org>
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

from dal_select2.views import Select2QuerySetView
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.html import escape
from rolepermissions.checkers import has_permission

from apps.challenge import MAX_MONO1_PER_QUALI

from ..models import FORMATION_KEYS, FORMATION_M2
from .mixins import ProfileMixin
from .standard import UserProfileFilterSet


class PersonAutocomplete(ProfileMixin, Select2QuerySetView):
    model = get_user_model()
    required_permission = 'user_view_list'
    choices = None
    widget_attrs = {'data-widget-maximum-values': 1, }

    def choice_label(self, choice):
        return choice.get_full_name()

    def choice_html(self, choice):
        """
        Override autocomplete_light to drop the 'escape' call over choice_label
        """
        return self.choice_html_format % (
            escape(self.choice_value(choice)),
            self.choice_label(choice))

    def get_queryset(self):
        if has_permission(self.request.user, self.required_permission):
            # Remove self.q to bypass Select2QuerySetView' wrong handling
            q = self.q if self.q else None
            del(self.q)
            qs = super(PersonAutocomplete, self).get_queryset()
            if q:
                qs = UserProfileFilterSet.filter_wide(qs, '', q)
            return qs
        else:
            raise PermissionDenied


class AllPersons(PersonAutocomplete):
    pass


class PersonsRelevantForSessions(PersonAutocomplete):
    def get_choices(self):
        qs = super(PersonsRelevantForSessions, self).get_choices()
        return qs.filter(
                Q(profile__formation__in=FORMATION_KEYS) |
                Q(profile__actor_for__isnull=False)
            )


class Helpers(PersonAutocomplete):
    widget_attrs = {'data-widget-maximum-values': MAX_MONO1_PER_QUALI, }

    def get_choices(self):
        qs = super(Helpers, self).get_choices()
        return qs.filter(
                Q(profile__formation__in=FORMATION_KEYS)
            )

    def choice_label(self, choice):
        return "{name} {icon}".format(
            name=choice.get_full_name(),
            icon=choice.profile.formation_icon())


class Leaders(PersonAutocomplete):
    def get_choices(self):
        qs = super(Leaders, self).get_choices()
        return qs.filter(
                Q(profile__formation=FORMATION_M2)
        )


class Actors(PersonAutocomplete):
    def get_choices(self):
        qs = super(Actors, self).get_choices()
        return qs.exclude(
            profile__actor_for__isnull=True
        )
