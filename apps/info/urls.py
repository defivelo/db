# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2017 Didier Raboud <me+defivelo@odyx.org>
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

from django.conf.urls import include
from django.urls import re_path
from django.views.decorators.cache import never_cache

from .views import (
    JSONNextQualifs,
    LogisticsExportView,
    LogisticsView,
    NextQualifs,
    QualifsCalendarExportView,
    QualifsCalendarView,
    SeasonExports,
    SeasonStatsExportView,
    SeasonStatsView,
)

urlpatterns = [
    re_path(
        r"^qualifs/$", never_cache(NextQualifs.as_view()), name="public-nextqualifs"
    ),
    re_path(
        r"^qualifs.json$",
        never_cache(JSONNextQualifs.as_view()),
        name="public-json-nextqualifs",
    ),
    re_path(
        r"^(?:(?P<year>[0-9]{4})_(?P<dv_season>[0-9]+)/)?",
        include(
            [
                re_path(
                    r"^$", never_cache(SeasonExports.as_view()), name="season-exports"
                ),
                # Calendar
                re_path(
                    r"^calendar/$",
                    never_cache(QualifsCalendarView.as_view()),
                    name="qualifs-calendar",
                ),
                re_path(
                    r"^calendar-(?P<format>[a-z]+)$",
                    never_cache(QualifsCalendarExportView.as_view()),
                    name="qualifs-calendar-export",
                ),
                # Statistiques de Mois
                re_path(
                    r"^stats/$",
                    never_cache(SeasonStatsView.as_view()),
                    name="season-stats",
                ),
                re_path(
                    r"^stats-(?P<format>[a-z]+)$",
                    never_cache(SeasonStatsExportView.as_view()),
                    name="season-stats-export",
                ),
                # Planification Logistique
                re_path(
                    r"^logistics/$",
                    never_cache(LogisticsView.as_view()),
                    name="logistics",
                ),
                re_path(
                    r"^logistics-(?P<format>[a-z]+)$",
                    never_cache(LogisticsExportView.as_view()),
                    name="logistics-export",
                ),
            ]
        ),
    ),
]
