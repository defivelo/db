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

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from dal_select2.views import Select2QuerySetView
from six import get_unbound_function

from apps.challenge import MAX_MONO1_PER_QUALI
from apps.common import MULTISELECTFIELD_REGEXP
from defivelo.roles import has_permission

from .. import FORMATION_KEYS, FORMATION_M2
from ..models import USERSTATUS_DELETED, UserProfile
from .mixins import ProfileMixin
from .standard import UserProfileFilterSet


class PersonAutocomplete(ProfileMixin, Select2QuerySetView):
    model = UserProfile
    required_permission = "user_view_list"
    choices = None
    widget_attrs = {
        "data-widget-maximum-values": 1,
    }

    def get_result_label(self, choice):
        return "{name}{ifcanton}".format(
            name=choice.user.get_full_name(),
            ifcanton=(
                (" (%s)" % choice.affiliation_canton)
                if choice and choice.affiliation_canton
                else ""
            ),
        )

    def get_queryset(self):
        if has_permission(self.request.user, self.required_permission):
            # Remove self.q to bypass Select2QuerySetView' wrong handling
            q = self.q if self.q else None
            del self.q
            qs = super(PersonAutocomplete, self).get_queryset()
            # Only non-deleted
            qs = qs.exclude(status=USERSTATUS_DELETED)
            if q:
                filter_wide = get_unbound_function(UserProfileFilterSet.filter_wide)
                qs = filter_wide(qs, "", q)
            return qs
        else:
            raise PermissionDenied


class AllPersons(PersonAutocomplete):
    pass


class PersonsRelevantForSessions(PersonAutocomplete):
    def get_queryset(self):
        qs = super(PersonsRelevantForSessions, self).get_queryset()
        qs = qs.filter(Q(formation__in=FORMATION_KEYS) | Q(actor_for__isnull=False))
        # Filtre par les cantons s'ils existent
        cantons = self.forwarded.get("cantons", [])
        if len(cantons) > 0:
            cantons_regexp = MULTISELECTFIELD_REGEXP % "|".join(
                [v for v in cantons if v]
            )
            qs = qs.filter(
                Q(activity_cantons__regex=cantons_regexp)
                | Q(affiliation_canton__in=cantons)
            )
        return qs.distinct()


class Helpers(PersonAutocomplete):
    widget_attrs = {
        "data-widget-maximum-values": MAX_MONO1_PER_QUALI,
    }

    def get_queryset(self):
        qs = super(Helpers, self).get_queryset()
        return qs.filter(formation__in=FORMATION_KEYS)

    def get_result_label(self, choice):
        return "{name} {icon}".format(
            name=choice.get_full_name(), icon=choice.formation_icon()
        )


class Leaders(PersonAutocomplete):
    def get_queryset(self):
        qs = super(Leaders, self).get_queryset()
        return qs.filter(formation=FORMATION_M2)


class Actors(PersonAutocomplete):
    def get_queryset(self):
        qs = super(Actors, self).get_queryset()
        return qs.exclude(actor_for__isnull=True).distinct()
