# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016 Didier Raboud <me+defivelo@odyx.org>
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

from django import forms

from apps.user.models import FORMATION_M1

from .models.availability import HelperSessionAvailability


class SessionChoiceField(object):
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', False)
        return super(SessionChoiceField, self).__init__(*args, **kwargs)

    def get_chosen_as(self, user):
        try:
            return user.availabilities.get(session=self.session).chosen_as
        except HelperSessionAvailability.DoesNotExist:
            pass


class LeaderChoiceField(SessionChoiceField, forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name()


class HelpersChoiceField(SessionChoiceField, forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return '%s%s' % (
            obj.get_full_name(),
            (
                ' (%s)' % obj.profile.formation
                if obj.profile.formation not in ['', FORMATION_M1]
                else ''
            ),
        )


class ActorChoiceField(SessionChoiceField, forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "{name} ({actor_for})".format(
             name=obj.get_full_name(),
             actor_for=obj.profile.actor_inline)
