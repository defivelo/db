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

from datetime import date

from django.core.urlresolvers import resolve
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from rolepermissions.mixins import HasPermissionsMixin
from stronghold.views import StrongholdPublicMixin

from apps.challenge.models.session import Session
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_SPRING
from apps.common.views import ExportMixin, PaginatorMixin
from defivelo.views.common import MenuView

from .exports import SeasonStatsExport


class PublicView(StrongholdPublicMixin):
    pass


class NextQualifs(PublicView, PaginatorMixin, ListView):
    template_name = 'info/next_qualifs.html'
    context_object_name = 'sessions'
    paginate_by = 6
    queryset = (
        Session.objects
        .filter(day__gte=date.today())
        .order_by('day', 'orga')
        .prefetch_related('orga')
    )


class StatsExportsMixin(MenuView, HasPermissionsMixin):
    def dispatch(self, *args, **kwargs):
        try:
            self.export_year = int(kwargs.pop('year'))
        except TypeError:
            self.export_year = date.today().year
        try:
            self.export_season = int(kwargs.pop('dv_season'))
        except TypeError:
            self.export_season = self.current_season()
        return super(StatsExportsMixin, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StatsExportsMixin, self).get_context_data(**kwargs)
        context['export_period'] = {
            'year': self.export_year,
            'season': self.export_season,
        }
        context['menu_category'] = 'exports'
        return context


class Exports(StatsExportsMixin, TemplateView):
    challenge_season_crud = 'challenge_season_crud'
    template_name = 'info/exports.html'

    def get_context_data(self, **kwargs):
        context = super(Exports, self).get_context_data(**kwargs)
        context['previous_period'] = {
            'year': self.export_year - (1 if self.export_season == DV_SEASON_SPRING else 0),
            'season': DV_SEASON_AUTUMN if self.export_season == DV_SEASON_SPRING else DV_SEASON_SPRING,
        }
        context['next_period'] = {
            'year': self.export_year + (1 if self.export_season == DV_SEASON_AUTUMN else 0),
            'season': DV_SEASON_AUTUMN if self.export_season == DV_SEASON_SPRING else DV_SEASON_SPRING,
        }
        context['nav_url'] = resolve(self.request.path).url_name
        try:
            context['dataset'] = self.get_dataset()
            context['dataset_title'] = self.get_dataset_title()
            context['dataset_exporturl'] = context['nav_url'] + '-export'
        except AttributeError:
            pass
        return context


class SeasonStatsView(SeasonStatsExport, Exports):
    pass


class SeasonStatsExportView(SeasonStatsExport, StatsExportsMixin, ExportMixin, ListView):
    pass