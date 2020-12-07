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

import uuid

from django.utils.translation import ugettext as u
from django.utils.translation import ugettext_lazy as _

from localflavor.ch.ch_states import STATE_CHOICES
from memoize import memoize

STATE_CHOICES_WITH_DEFAULT = tuple(
    list(
        (
            (
                "",
                "---------",
            ),
        )
    )
    + list(STATE_CHOICES)
)

FORMATION_M1 = "M1"
FORMATION_M2 = "M2"

FORMATION_CHOICES = (
    ("", "----------"),
    (FORMATION_M1, _("Moniteur 1")),
    (FORMATION_M2, _("Moniteur 2")),
)
FORMATION_KEYS = [k[0] for k in FORMATION_CHOICES if k[0] != ""]


@memoize()
def formation_short(formation, real_gettext=False):
    if formation == FORMATION_M1:
        return (
            # Translators: FORMATION_M1 - Moniteur 1
            u("M1")
            if real_gettext
            else _("M1")
        )
    elif formation == FORMATION_M2:
        return (
            # Translators: FORMATION_M2 - Moniteur 2
            u("M2")
            if real_gettext
            else _("M2")
        )
    return ""


def get_new_username():
    return uuid.uuid4().hex[0:30]
