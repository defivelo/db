# -*- coding: utf-8 -*-
#
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
from __future__ import unicode_literals

from django.conf.urls import include, url
from django.views.decorators.cache import never_cache

from .views import (
    Exports, NextQualifs, OrgaInvoicesExportView, OrgaInvoicesView, QualifsCalendar, SeasonStatsExportView,
    SeasonStatsView,
)

urlpatterns = [
    url(r'^qualifs/$',
        never_cache(NextQualifs.as_view()),
        name='public-nextqualifs'),
    url(r'^(?:(?P<year>[0-9]{4})/(?P<dv_season>[0-9]+)/)?',
        include([
            url(r'^$', never_cache(Exports.as_view()), name='exports'),
            url(r'^calendar/$', never_cache(QualifsCalendar.as_view()), name='qualifs-calendar'),
            # Statistiques de Saison
            url(r'^stats/$',
                never_cache(SeasonStatsView.as_view()), name='season-stats'),
            url(r'^stats-(?P<format>[a-z]+)$',
                never_cache(SeasonStatsExportView.as_view()), name='season-stats-export'),
            # Facturation établissements
            url(r'^orga-invoice/$',
                never_cache(OrgaInvoicesView.as_view()), name='orga-invoices'),
            url(r'^orga-invoice-(?P<format>[a-z]+)$',
                never_cache(OrgaInvoicesExportView.as_view()), name='orga-invoices-export'),
        ]))
]
