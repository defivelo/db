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

from django.utils.translation import gettext_lazy as _

AVAILABILITY_FIELDKEY_HELPER_PREFIX = "avail-h{hpk}-"
STAFF_FIELDKEY_HELPER_PREFIX = "staff-h{hpk}-"
SUPERLEADER_FIELDKEY_HELPER_PREFIX = "superleader-h{hpk}-"
CHOICE_FIELDKEY_HELPER_PREFIX = "choice-h{hpk}-"
CONFLICT_FIELDKEY_HELPER_PREFIX = "conflict-h{hpk}-"
SEASON_WORKWISH_FIELDKEY = "season-ww-h{hpk}"

AVAILABILITY_FIELDKEY = AVAILABILITY_FIELDKEY_HELPER_PREFIX + "s{spk}"
STAFF_FIELDKEY = STAFF_FIELDKEY_HELPER_PREFIX + "s{spk}"
SUPERLEADER_FIELDKEY = SUPERLEADER_FIELDKEY_HELPER_PREFIX + "s{spk}"
CHOICE_FIELDKEY = CHOICE_FIELDKEY_HELPER_PREFIX + "s{spk}"
CONFLICT_FIELDKEY = CONFLICT_FIELDKEY_HELPER_PREFIX + "s{spk}"

MAX_MONO1_PER_QUALI = 2

CHOSEN_AS_NOT = 0
CHOSEN_AS_LEGACY = 1
CHOSEN_AS_ACTOR = 2
CHOSEN_AS_HELPER = 3
CHOSEN_AS_LEADER = 4
CHOSEN_AS_REPLACEMENT = 5
CHOICE_CHOICES = (
    (CHOSEN_AS_NOT, _("Pas choisi")),
    (CHOSEN_AS_LEGACY, _("Choisi")),  # À ne pas réutiliser
    (CHOSEN_AS_ACTOR, _("Comme intervenant")),
    (CHOSEN_AS_REPLACEMENT, _("Moniteur de Secours")),
    (CHOSEN_AS_HELPER, _("Moniteur 1")),
    (CHOSEN_AS_LEADER, _("Moniteur 2")),
)

CHOSEN_KEYS = [c[0] for c in CHOICE_CHOICES if c[0] != CHOSEN_AS_NOT]
