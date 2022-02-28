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

from datetime import date

from django.http import JsonResponse
from django.urls import resolve
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView

from rolepermissions.mixins import HasPermissionsMixin
from stronghold.decorators import public
from stronghold.views import StrongholdPublicMixin

from apps.challenge.models.session import Session
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_SPRING
from apps.common.views import ExportMixin, PaginatorMixin
from defivelo.views.common import MenuView

from . import utils
from .exports import (
    LogisticsExport,
    QualifsCalendarExport,
    SeasonSessionsMixin,
    SeasonStatsExport,
)
from .forms import CantonFilterForm


class SessionsPublicView(StrongholdPublicMixin):
    def get_queryset(self):
        # This needs to be a get_queryset to make sure the date.today() is evaluated at view time, not at start time.
        return (
            Session.objects.filter(day__gte=date.today())
            .order_by("day", "orga")
            .prefetch_related("orga")
        )

    @method_decorator(public)
    @method_decorator(xframe_options_exempt)
    def dispatch(self, *args, **kwargs):
        return super(SessionsPublicView, self).dispatch(*args, **kwargs)


class NextQualifs(SessionsPublicView, PaginatorMixin, ListView):
    template_name = "info/next_qualifs.html"
    paginate_by = 8
    context_object_name = "sessions"


class JSONNextQualifs(SessionsPublicView, TemplateView):
    def render_to_response(self, context, **response_kwargs):
        sessions = []
        for session in self.get_queryset().all():
            session_representation = {
                "canton": session.orga.address_canton,
                "date": session.day,
                "begin": session.begin,
                "orga": {"name": session.orga.name, "abbr": session.orga.abbr},
                "city": session.city,
            }
            sessions.append(session_representation)
        return JsonResponse({"sessions": sessions}, **response_kwargs)


class SeasonExportsMixin(MenuView):
    def dispatch(self, *args, **kwargs):
        try:
            self.export_year = int(kwargs.pop("year"))
        except TypeError:
            self.export_year = date.today().year
        try:
            self.export_season = int(kwargs.pop("dv_season"))
        except TypeError:
            self.export_season = self.current_season()
        return super(SeasonExportsMixin, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SeasonExportsMixin, self).get_context_data(**kwargs)
        context["export_period"] = {
            "year": self.export_year,
            "season": self.export_season,
        }
        context["previous_period"] = {
            "year": self.export_year
            - (1 if self.export_season == DV_SEASON_SPRING else 0),
            "season": DV_SEASON_AUTUMN
            if self.export_season == DV_SEASON_SPRING
            else DV_SEASON_SPRING,
        }
        context["next_period"] = {
            "year": self.export_year
            + (1 if self.export_season == DV_SEASON_AUTUMN else 0),
            "season": DV_SEASON_AUTUMN
            if self.export_season == DV_SEASON_SPRING
            else DV_SEASON_SPRING,
        }
        context["nav_url"] = resolve(self.request.path).url_name
        context["dataset_exporturl"] = context["nav_url"] + "-export"
        context["menu_category"] = "statistics"
        context["submenu_category"] = "statistics-season"
        return context


class IfDatasetExportMixin(object):
    def get_context_data(self, **kwargs):
        context = super(IfDatasetExportMixin, self).get_context_data(**kwargs)
        try:
            context["dataset"] = self.get_dataset(html=True)
            context["dataset_title"] = self.get_dataset_title()
        except AttributeError:
            pass
        return context


class SeasonExports(
    SeasonExportsMixin, HasPermissionsMixin, IfDatasetExportMixin, TemplateView
):
    required_permission = "challenge_season_crud"
    template_name = "info/season_exports.html"

    def get_context_data(self, **kwargs):
        context = super(SeasonExports, self).get_context_data(**kwargs)
        context["submenu_category"] = "statistics-season"
        return context


class QualifsCalendarView(SeasonSessionsMixin, SeasonExportsMixin, ListView):
    limit_to_my_cantons = False
    template_name = "info/qualifs_calendar.html"
    context_object_name = "sessions"

    def post(self, request, *args, **kwargs):
        form = CantonFilterForm(request.POST)
        if form.is_valid():
            self.cantons = form.cleaned_data["canton"]
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(QualifsCalendarView, self).get_context_data(**kwargs)
        context["menu_category"] = "season"
        context["submenu_category"] = "qualifs-calendar"
        # Add the form for picking a new helper
        context["form"] = CantonFilterForm()
        our_sessions = context["sessions"]
        if hasattr(self, "cantons") and len(self.cantons) > 0:
            our_sessions = our_sessions.filter(orga__address_canton__in=self.cantons)
        our_sessions = list(our_sessions)

        if len(our_sessions) == 0:
            return context

        context["legend_cantons"] = {s.orga.address_canton: "" for s in our_sessions}

        context["date_sessions"] = utils._get_qualifs_calendar_structured_data(
            our_sessions
        )

        return context


class QualifsCalendarExportView(
    QualifsCalendarExport, SeasonExportsMixin, ExportMixin, ListView
):
    def get_context_data(self, **kwargs):
        context = super(QualifsCalendarExportView, self).get_context_data(**kwargs)
        our_sessions = context["session_list"]
        if hasattr(self, "cantons") and len(self.cantons) > 0:
            our_sessions = our_sessions.filter(orga__address_canton__in=self.cantons)
        our_sessions = list(our_sessions)

        if len(our_sessions) == 0:
            return context

        context["legend_cantons"] = {s.orga.address_canton: "" for s in our_sessions}
        context["date_sessions"] = utils._get_qualifs_calendar_structured_data(
            our_sessions
        )

        return context


class SeasonStatsView(SeasonStatsExport, SeasonExports):
    pass


class SeasonStatsExportView(
    SeasonStatsExport, SeasonExportsMixin, ExportMixin, ListView
):
    pass


class LogisticsView(LogisticsExport, SeasonExports):
    pass


class LogisticsExportView(LogisticsExport, SeasonExportsMixin, ExportMixin, ListView):
    pass
