# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2017,2020 Didier Raboud <didier.raboud@liip.ch>
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

from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.template.defaultfilters import date as datefilter
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from tablib import Dataset

from apps.challenge.models.session import Session
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_LAST_SPRING_MONTH, DV_STATE_CHOICES
from apps.orga.models import Organization
from defivelo.roles import user_cantons
from defivelo.templatetags.dv_filters import (
    season_month_end,
    season_month_start,
    season_verb,
)

linktxt = '<a href="{url}">{content}</a>'


class SeasonSessionsMixin(object):
    limit_to_my_cantons = True

    def get_queryset(self):
        begin = date(self.export_year, 1, 1)
        if self.export_season == DV_SEASON_AUTUMN:
            begin = date(self.export_year, DV_SEASON_LAST_SPRING_MONTH + 1, 1)
        end = date(self.export_year, DV_SEASON_LAST_SPRING_MONTH + 1, 1) - timedelta(
            days=1
        )
        if self.export_season == DV_SEASON_AUTUMN:
            end = date(self.export_year, 12, 31)
        sessions = (
            Session.objects.filter(
                day__gte=begin,
                day__lte=end,
            )
            .order_by("day", "begin")
            .prefetch_related("orga")
        )
        if self.limit_to_my_cantons:
            sessions = sessions.filter(
                orga__address_canton__in=user_cantons(self.request.user)
            )
        return sessions


class QualifsCalendarExport(SeasonSessionsMixin):
    def get_dataset_title(self):
        return "Calendar export dataset title"

    @property
    def export_filename(self):
        return "%s-%s-%s" % (
            _("Calendar"),
            self.export_year,
            season_verb(self.export_season),
        )

    def get_dataset(self, html=False):
        dataset = Dataset()
        dataset.headers = [
            gettext("Semaine"),
            gettext("Lundi"),
            gettext("Mardi"),
            gettext("Mercredi"),
            gettext("Jeudi"),
            gettext("Vendredi"),
            gettext("Samedi"),
            gettext("Dimanche"),
        ]

        calendar_data = self.get_context_data()["date_sessions"]

        row = []
        for day_data in calendar_data:
            day = day_data["day"]

            if day.weekday() == 0:
                row.append(day.strftime("%W"))

            text = day.strftime("%Y-%m-%d")

            for session in day_data["sessions"]:
                text += "\n{} {} {}".format(
                    session.begin if session.begin else "",
                    session.orga.abbr if session.orga.abbr else session.orga.name,
                    session.orga.address_canton,
                )
            row.append(text)

            if day.weekday() == 6:
                dataset.append(row)
                row = []

        return dataset


class SeasonStatsExport(SeasonSessionsMixin):
    def get_dataset_title(self):
        return "{title} - {month_start} à {month_end} {year}".format(
            title=(gettext("Statistiques")),
            year=self.export_year,
            month_start=season_month_start(self.export_season),
            month_end=season_month_end(self.export_season),
        )

    @property
    def export_filename(self):
        return "%s-%s-%s" % (
            _("Stats_Mois"),
            self.export_year,
            season_verb(self.export_season),
        )

    def get_dataset(self, html=False):
        dataset = Dataset()
        dataset.headers = [
            gettext("Canton"),
            gettext("Établissements"),
            gettext("Sessions"),
            gettext("Qualifs"),
            gettext("Nombre d’élèves"),
            gettext("Prêts de vélos"),
            gettext("Prêts de casques"),
            gettext("Nombre de personnes ayant exercé"),
            gettext("… comme moniteurs 2"),
            gettext("… comme moniteurs 1"),
            gettext("… comme intervenants"),
        ]
        volunteers = get_user_model().objects
        orgas = Organization.objects
        object_list = self.get_queryset()
        for canton, canton_verb in DV_STATE_CHOICES:
            cantonal_sessions = object_list.filter(
                orga__address_canton=canton
            ).annotate(
                n_qualifs=Count("qualifications"),
                n_participants=Sum("qualifications__n_participants"),
                n_bikes=Sum("qualifications__n_bikes"),
                n_helmets=Sum("qualifications__n_helmets"),
            )
            n_sessions = cantonal_sessions.count()
            if n_sessions > 0:
                sessions_pks = cantonal_sessions.values_list("id", flat=True)
                dataset.append(
                    [
                        canton,
                        orgas.filter(sessions__in=sessions_pks).distinct().count(),
                        n_sessions,
                        cantonal_sessions.aggregate(total=Sum("n_qualifs"))["total"],
                        cantonal_sessions.aggregate(total=Sum("n_participants"))[
                            "total"
                        ],
                        cantonal_sessions.aggregate(total=Sum("n_bikes"))["total"],
                        cantonal_sessions.aggregate(total=Sum("n_helmets"))["total"],
                        volunteers.filter(
                            Q(qualifs_mon2__session__in=sessions_pks)
                            | Q(qualifs_mon1__session__in=sessions_pks)
                            | Q(qualifs_actor__session__in=sessions_pks)
                        )
                        .distinct()
                        .count(),
                        volunteers.filter(qualifs_mon2__session__in=sessions_pks)
                        .distinct()
                        .count(),
                        volunteers.filter(qualifs_mon1__session__in=sessions_pks)
                        .distinct()
                        .count(),
                        volunteers.filter(qualifs_actor__session__in=sessions_pks)
                        .distinct()
                        .count(),
                    ]
                )
        return dataset


class LogisticsExport(SeasonSessionsMixin):
    def get_dataset_title(self):
        return "{title} - {month_start} à {month_end} {year}".format(
            title=(gettext("Planification logistique")),
            year=self.export_year,
            month_start=season_month_start(self.export_season),
            month_end=season_month_end(self.export_season),
        )

    @property
    def export_filename(self):
        return "%s-%s-%s-%s" % (
            gettext("Logistique"),
            gettext("Mois"),
            self.export_year,
            season_verb(self.export_season),
        )

    def get_dataset(self, html=False):
        dataset = Dataset()
        dataset.headers = [
            gettext("Canton"),
            gettext("Établissement"),
            gettext("Lieu"),
            gettext("Date"),
            gettext("Heure"),
            gettext("Classes"),
            gettext("Participants"),
            gettext("Vélos loués"),
            gettext("Casques loués"),
            gettext("Logistique vélos"),
            gettext("N° de contact vélos"),
        ]
        sessions = self.get_queryset()
        sessions = sessions.annotate(
            n_qualifs=Count("qualifications"),
            n_participants=Sum("qualifications__n_participants"),
            n_bikes=Sum("qualifications__n_bikes"),
            n_helmets=Sum("qualifications__n_helmets"),
        )
        for session in sessions:
            season = session.season
            url = None
            if season and html:
                url = reverse(
                    "session-detail",
                    kwargs={"seasonpk": season.pk, "pk": session.id},
                )
            datetxt = datefilter(session.day, settings.DATE_FORMAT_COMPACT)
            timetxt = datefilter(session.begin, settings.TIME_FORMAT_SHORT)
            dataset.append(
                [
                    session.orga.address_canton,
                    session.orga.ifabbr if html else session.orga.name,
                    session.city,
                    mark_safe(linktxt.format(url=url, content=datetxt))
                    if url
                    else datetxt,
                    mark_safe(linktxt.format(url=url, content=timetxt))
                    if url
                    else timetxt,
                    session.n_qualifs,
                    session.n_participants,
                    session.n_bikes,
                    session.n_helmets,
                    session.bikes_concept,
                    session.bikes_phone,
                ]
            )
        return dataset
