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

from django.utils.translation import ugettext_lazy as _

AVAILABILITY_FIELDKEY_HELPER_PREFIX = 'avail-h{hpk}-'
STAFF_FIELDKEY_HELPER_PREFIX = 'staff-h{hpk}-'

AVAILABILITY_FIELDKEY = AVAILABILITY_FIELDKEY_HELPER_PREFIX + 's{spk}'
STAFF_FIELDKEY = STAFF_FIELDKEY_HELPER_PREFIX + 's{spk}'

MAX_MONO1_PER_QUALI = 2

SHORTCODE_MON1 = '1'
SHORTCODE_MON2 = '2'
SHORTCODE_ACTOR = 'A'
SHORTCODE_SELECTED = 'x'

CHOSEN_AS_NOT = 0
CHOSEN_AS_LEGACY = 1
CHOSEN_AS_ACTOR = 2
CHOSEN_AS_HELPER = 3
CHOSEN_AS_LEADER = 4
CHOICE_CHOICES = (
    (CHOSEN_AS_LEADER, _('Moniteur 2')),
    (CHOSEN_AS_HELPER, _('Moniteur 1')),
    (CHOSEN_AS_ACTOR, _('Comme intervenant')),
    (CHOSEN_AS_LEGACY, _('Choisi')),  # À ne pas réutiliser
    (CHOSEN_AS_NOT, _('Pas choisi')),
)
