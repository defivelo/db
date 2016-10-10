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

from autocomplete_light.shortcuts import register as al_register
from django.utils.translation import ugettext_lazy as _

from .views.autocomplete import (
    Actors, AllPersons, Helpers, Leaders, PersonsRelevantForSeason,
    PersonsRelevantForSessions,
)

ac_placeholder = _('type some text to search in this autocomplete')

al_register(AllPersons)
al_register(PersonsRelevantForSeason)
al_register(PersonsRelevantForSessions)
al_register(Helpers)
al_register(Leaders)
al_register(Actors)
