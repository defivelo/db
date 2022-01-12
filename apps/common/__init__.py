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

from django.utils.translation import ugettext_lazy as _

from localflavor.ch.ch_states import STATE_CHOICES

STDGLYPHICON = (
    '<span class="glyphicon glyphicon-{icon}" aria-hidden="true"'
    '      title="{title}"></span>'
)

# Cantons où DÉFI VÉLO est actif
DV_STATES = [
    "VD",
    "VS",
    "FR",
    "NE",
    "GE",
    "JU",
    "BS",
    "SG",
    "ZH",
    "BE",
    "LU",
    "AR",
    "SO",
    "AG",
    "BL",
    "GR",
    "SZ",
    "ZG",
]

DV_STATE_COLORS = {
    None: "#000",
    # Dans le même ordre que la charte graphique
    "VD": "#64B984",
    "NE": "#EF7F5E",
    "FR": "#97669E",
    "GE": "#FECC01",
    "JU": "#E84653",
    "BE": "#5EC5F2",
    "VS": "#EF86A1",
    "BS": "#5DBDB2",
    "UR": "#206FB7",
    "SZ": "#E84C0F",
    "OW": "#00595F",
    "NW": "#663265",
    "LU": "#9DC762",
    "AI": "#1D1D1B",
    "AR": "#F7AE1A",
    "SH": "#A4D1A6",
    "BL": "#FEED40",
    "TG": "#363777",
    "SO": "#C61650",
    "ZG": "#00837E",
    "TI": "#B0CB22",
    "GL": "#8075B4",
    "AG": "#8075B4",
    "GR": "#E7206A",
    "SG": "#608A9B",
    "ZH": "#7ABEE4",
    "default": "#56A7DC",
}

DV_STATE_CHOICES = [c for c in STATE_CHOICES if c[0] in DV_STATES]

DV_STATE_CHOICES_WITH_DEFAULT = tuple(
    list(
        (
            (
                "",
                "---------",
            ),
        )
    )
    + list(DV_STATE_CHOICES)
)

MULTISELECTFIELD_REGEXP = "(^|,)%s(,|$)"

DV_LANGUAGES = LANGUAGES = (
    ("fr", _("French")),
    ("de", _("German")),
    ("it", _("Italian")),
    ("en", _("English")),
)

DV_LANGUAGES_WITH_DEFAULT = tuple(
    list(
        (
            (
                "",
                "---------",
            ),
        )
    )
    + list(DV_LANGUAGES)
)

DV_SEASON_SPRING = 1
# DV_SEASON_SUMMER = 2
DV_SEASON_AUTUMN = 3
# DV_SEASON_WINTER = 4

DV_SEASON_CHOICES = (
    (DV_SEASON_SPRING, _("Printemps")),
    (DV_SEASON_AUTUMN, _("Automne")),
)

# Dernier mois des saisons de Printemps
DV_SEASON_LAST_SPRING_MONTH = 7

# État des saisons
DV_SEASON_STATE_PLANNING = 1  # RW for StateManager, -- for helpers
DV_SEASON_STATE_OPEN = 2  # RW for StateManage, RW for helpers
DV_SEASON_STATE_RUNNING = 3  # RW for SM, R- for helpers
DV_SEASON_STATE_FINISHED = 4  # RW for SM, R-- for helpers
DV_SEASON_STATE_ARCHIVED = 5  # R- for SM, R-- for helpers

DV_SEASON_STATES = (
    (DV_SEASON_STATE_PLANNING, _("Planification (invisible)")),
    (DV_SEASON_STATE_OPEN, _("Annoncé (rentrée des disponibilités)")),
    (DV_SEASON_STATE_RUNNING, _("En cours (corrections que par chargé·e·s de projet)")),
    (DV_SEASON_STATE_FINISHED, _("Terminé")),
    (DV_SEASON_STATE_ARCHIVED, _("Archivé")),
)
