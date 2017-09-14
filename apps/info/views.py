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

from datetime import date, timedelta

from django.core.urlresolvers import resolve
from django.views.generic.base import TemplateView
from django.views.generic.dates import MonthArchiveView
from django.views.generic.list import ListView
from rolepermissions.mixins import HasPermissionsMixin
from stronghold.views import StrongholdPublicMixin

from apps.challenge.models.session import Session
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_SPRING
from apps.common.views import ExportMixin, PaginatorMixin
from defivelo.roles import user_cantons
from defivelo.views.common import MenuView

from .exports import (
    ExpensesExport, LogisticsExport, OrgaInvoicesExport, SalariesExport, SeasonSessionsMixin, SeasonStatsExport,
)


class PublicView(StrongholdPublicMixin):
    pass


class NextQualifs(PublicView, PaginatorMixin, ListView):
    template_name = 'info/next_qualifs.html'
    context_object_name = 'sessions'
    paginate_by = 8
    queryset = (
        Session.objects
        .filter(day__gte=date.today())
        .order_by('day', 'orga')
        .prefetch_related('orga')
    )


class MonthExportsMixin(HasPermissionsMixin, MenuView, MonthArchiveView):
    required_permission = 'challenge_season_crud'
    date_field = "day"
    month_format = '%m'
    allow_empty = True
    allow_future = True

    def get_queryset(self):
        return (
            Session.objects
            .filter(orga__address_canton__in=user_cantons(self.request.user))
            .order_by('day', 'orga', 'begin')
            .prefetch_related(
                'orga',
                'qualifications',
                'qualifications__helpers',
                )
        )

    def get_month(self):
        month = super(MonthExportsMixin, self).get_month()
        return month if month is not None else str(date.today().month)

    def get_year(self):
        year = super(MonthExportsMixin, self).get_year()
        return year if year is not None else str(date.today().year)

    def get_context_data(self, **kwargs):
        context = super(MonthExportsMixin, self).get_context_data(**kwargs)
        context['nav_url'] = resolve(self.request.path).url_name
        context['dataset_exporturl'] = context['nav_url'] + '-export'
        context['menu_category'] = 'exports'
        return context


class SeasonExportsMixin(MenuView):
    def dispatch(self, *args, **kwargs):
        try:
            self.export_year = int(kwargs.pop('year'))
        except TypeError:
            self.export_year = date.today().year
        try:
            self.export_season = int(kwargs.pop('dv_season'))
        except TypeError:
            self.export_season = self.current_season()
        return super(SeasonExportsMixin, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SeasonExportsMixin, self).get_context_data(**kwargs)
        context['export_period'] = {
            'year': self.export_year,
            'season': self.export_season,
        }
        context['previous_period'] = {
            'year': self.export_year - (1 if self.export_season == DV_SEASON_SPRING else 0),
            'season': DV_SEASON_AUTUMN if self.export_season == DV_SEASON_SPRING else DV_SEASON_SPRING,
        }
        context['next_period'] = {
            'year': self.export_year + (1 if self.export_season == DV_SEASON_AUTUMN else 0),
            'season': DV_SEASON_AUTUMN if self.export_season == DV_SEASON_SPRING else DV_SEASON_SPRING,
        }
        context['nav_url'] = resolve(self.request.path).url_name
        context['dataset_exporturl'] = context['nav_url'] + '-export'
        context['menu_category'] = 'exports'
        return context


class QualifsCalendar(SeasonSessionsMixin, SeasonExportsMixin, ListView):
    limit_to_my_cantons = False
    template_name = 'info/qualifs_calendar.html'
    context_object_name = 'sessions'

    def get_context_data(self, **kwargs):
        context = super(QualifsCalendar, self).get_context_data(**kwargs)
        our_sessions = list(context['sessions'])
        if len(our_sessions) == 0:
            return context
        context['date_sessions'] = []
        context['legend_cantons'] = {s.orga.address_canton: '' for s in our_sessions}
        # Get to its monday (see https://stackoverflow.com/questions/1622038/find-mondays-date-with-python)
        first_session_day = our_sessions[0].day
        first_monday = first_session_day + timedelta(days=-first_session_day.weekday())
        thisday = first_monday
        offset = 0
        while len(our_sessions) > 0:
            thisday = first_monday + timedelta(days=offset)
            struct = {
                'day': thisday,
                'sessions': []
            }
            while our_sessions and our_sessions[0].day == thisday:
                struct['sessions'].append(our_sessions.pop(0))
            context['date_sessions'].append(struct)
            # Go to next day
            offset = offset + 1
        # Fill in the missing days
        while thisday.weekday() != 6:
            thisday = first_monday + timedelta(days=offset)
            context['date_sessions'].append({
                'day': thisday,
                'sessions': []
            })
            offset = offset + 1

        context['menu_category'] = 'season'
        context['submenu_category'] = 'qualifs-calendar'
        return context


class IfDatasetExportMixin(object):
    def get_context_data(self, **kwargs):
        context = super(IfDatasetExportMixin, self).get_context_data(**kwargs)
        try:
            context['dataset'] = self.get_dataset(html=True)
            context['dataset_title'] = self.get_dataset_title()
        except AttributeError:
            pass
        return context


class MonthExports(IfDatasetExportMixin, MonthExportsMixin):
    template_name = 'info/month_exports.html'

    def get_context_data(self, **kwargs):
        context = super(MonthExports, self).get_context_data(**kwargs)
        context['submenu_category'] = 'exports-month'
        return context


class SalariesView(SalariesExport, MonthExports):
    pass


class SalariesExportView(SalariesExport, MonthExports, ExportMixin, ListView):
    pass


class ExpensesView(ExpensesExport, MonthExports):
    pass


class ExpensesExportView(ExpensesExport, MonthExports, ExportMixin, ListView):
    pass


class SeasonExports(SeasonExportsMixin, HasPermissionsMixin,
                    IfDatasetExportMixin, TemplateView):
    required_permission = 'challenge_season_crud'
    template_name = 'info/season_exports.html'

    def get_context_data(self, **kwargs):
        context = super(SeasonExports, self).get_context_data(**kwargs)
        context['submenu_category'] = 'exports-month'
        return context


class SeasonStatsView(SeasonStatsExport, SeasonExports):
    pass


class SeasonStatsExportView(SeasonStatsExport, SeasonExportsMixin, ExportMixin, ListView):
    pass


class OrgaInvoicesView(OrgaInvoicesExport, SeasonExports):
    pass


class OrgaInvoicesExportView(OrgaInvoicesExport, SeasonExportsMixin, ExportMixin, ListView):
    pass


class LogisticsView(LogisticsExport, SeasonExports):
    pass


class LogisticsExportView(LogisticsExport, SeasonExportsMixin, ExportMixin, ListView):
    pass
