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

from django.utils.translation import ugettext_lazy as _
from memoize import memoize
from rolepermissions.checkers import has_permission as uncached_has_permission
from rolepermissions.roles import AbstractUserRole

from apps.common import DV_STATES


# Override 'has_permission' from rolepermissions to add memoization for performance reasons
@memoize()
def has_permission(user, permission_name):
    return uncached_has_permission(user, permission_name)


@memoize()
def user_cantons(user):
    if has_permission(user, 'cantons_all'):
        return DV_STATES
    elif has_permission(user, 'cantons_mine'):
        return [m.canton for m in user.managedstates.all()]
    else:
        raise LookupError("No user cantons")


class StateManager(AbstractUserRole):
    available_permissions = {
        'cantons_all': False,
        'cantons_mine': True,

        'user_view_list': True,
        'user_detail_other': True,
        'user_edit_other': True,
        'user_crud_dv_public_fields': True,
        'user_crud_dv_private_fields': True,
        'user_create': True,

        'orga_crud': True,

        'challenge_season_crud': True,
        'challenge_session_crud': True,
        'challenge_season_see_state_planning': True,
    }


class PowerUser(AbstractUserRole):
    available_permissions = {
        'cantons_all': True,
        'cantons_mine': True,

        'user_view_list': True,
        'user_detail_other': True,
        'user_edit_other': True,
        'user_create': True,
        'user_crud_dv_public_fields': True,
        'user_crud_dv_private_fields': True,
        'user_can_send_credentials': True,
        'user_can_resend_credentials': True,
        'user_deletions': True,
        'user_set_role': True,

        'home_article_crud': True,

        'orga_crud': True,

        'challenge_season_crud': True,
        'challenge_session_crud': True,
        'challenge_season_see_state_planning': True,
    }


DV_AVAILABLE_ROLES = (
    (None, _('Aucun rôle')),
    ('state_manager', _('Chargé·e de projet')),
    ('power_user', _('Super-utilisa·teur·trice')),
)
