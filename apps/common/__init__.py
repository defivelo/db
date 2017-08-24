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

from operator import itemgetter
from localflavor.ch.ch_states import STATE_CHOICES
from django.utils.translation import ugettext_lazy as _

# Cantons où DÉFI VÉLO est actif
DV_STATES = ['VD', 'VS', 'FR', 'NE', 'GE', 'JU',
             'BS', 'SG', 'ZH', 'BE', 'LU', 'AR',
             'VS-OW',  # Haut-Valais
             ]

# "faux" cantons pour DÉFI VÉLO
DV_ADDITIONAL_STATES = [
    ('VS-OW', _('Haut-Valais')),
]

DV_STATE_CHOICES = [c for c in STATE_CHOICES if c[0] in DV_STATES] + \
    DV_ADDITIONAL_STATES

DV_STATE_CHOICES_WITH_DEFAULT = tuple(
    list((('', '---------',),)) +
    list(DV_STATE_CHOICES)
)

MULTISELECTFIELD_REGEXP = "(^|,)%s(,|$)"

DV_LANGUAGES = LANGUAGES = (
    ('fr', _('French')),
    ('de', _('German')),
    ('it', _('Italian')),
    ('en', _('English')),
)

DV_LANGUAGES_WITH_DEFAULT = tuple(
    list((('', '---------',),)) +
    list(DV_LANGUAGES)
)


def dv_sort_by_trad(tup):
    return tuple(sorted(tup, key=itemgetter(1)))
