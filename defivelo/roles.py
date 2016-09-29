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

from rolepermissions.roles import AbstractUserRole


class PowerUser(AbstractUserRole):
    available_permissions = {
        'user_view_list': True,
        'user_detail_other': True,
        'user_edit_other': True,
        'user_create': True,
        'user_crud_dv_public_fields': True,
        'user_crud_dv_private_fields': True,
        'user_can_send_credentials': True,

        'home_article_crud': True,

        'orga_crud': True,

        'challenge_season_crud': True,
        'challenge_session_crud': True,
    }
