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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models import Count, Q, Sum
from django.template.defaultfilters import date as datefilter
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, ugettext as u
from tablib import Dataset

from apps.challenge.models.session import Session
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_LAST_SPRING_MONTH, DV_STATE_CHOICES
from apps.orga.models import Organization
from defivelo.templatetags.dv_filters import season_verb


class SeasonExportMixin(object):
    def get_queryset(self):
        begin = date(self.export_year, 1, 1)
        if self.export_season == DV_SEASON_AUTUMN:
            begin = date(self.export_year, DV_SEASON_LAST_SPRING_MONTH + 1, 1)
        end = date(self.export_year, DV_SEASON_LAST_SPRING_MONTH + 1, 1) - timedelta(days=1)
        if self.export_season == DV_SEASON_AUTUMN:
            end = date(self.export_year, 12, 31)
        return (
            Session.objects
            .filter(day__gte=begin, day__lte=end)
            .order_by('day', 'begin')
            .prefetch_related('orga')
        )


class SeasonStatsExport(SeasonExportMixin):
    def get_dataset_title(self):
        return _('Statistiques de la saison {season} {year}').format(
            season=season_verb(self.export_season),
            year=self.export_year
        )

    @property
    def export_filename(self):
        return '%s-%s-%s' % (
            _('Stats_Saison'),
            self.export_year,
            season_verb(self.export_season)
        )

    def get_dataset(self, html=False):
        dataset = Dataset()
        # Prépare le fichier
        dataset.append([
            u('Canton'),
            u('Établissements'),
            u('Sessions'),
            u('Qualifs'),
            u('Nombre d\'élèves'),
            u('Prêts de vélos'),
            u('Prêts de casques'),
            u('Nombre de personnes ayant exercé'),
            u('… comme moniteurs 2'),
            u('… comme moniteurs 1'),
            u('… comme intervenants'),
        ])
        volunteers = get_user_model().objects
        orgas = Organization.objects
        object_list = self.get_queryset()
        for (canton, canton_verb) in DV_STATE_CHOICES:
            cantonal_sessions = (
                object_list
                .filter(orga__address_canton=canton)
                .annotate(
                    n_qualifs=Count('qualifications'),
                    n_participants=Sum('qualifications__n_participants'),
                    n_bikes=Sum('qualifications__n_bikes'),
                    n_helmets=Sum('qualifications__n_helmets'),
                )
            )
            n_sessions = cantonal_sessions.count()
            if n_sessions > 0:
                sessions_pks = cantonal_sessions.values_list('id', flat=True)
                dataset.append([
                    canton,
                    orgas.filter(sessions__in=sessions_pks).distinct().count(),
                    n_sessions,
                    cantonal_sessions.aggregate(total=Sum('n_qualifs'))['total'],
                    cantonal_sessions.aggregate(total=Sum('n_participants'))['total'],
                    cantonal_sessions.aggregate(total=Sum('n_bikes'))['total'],
                    cantonal_sessions.aggregate(total=Sum('n_helmets'))['total'],
                    volunteers.filter(
                        Q(qualifs_mon2__session__in=sessions_pks) |
                        Q(qualifs_mon1__session__in=sessions_pks) |
                        Q(qualifs_actor__session__in=sessions_pks)
                        ).distinct().count(),
                    volunteers.filter(qualifs_mon2__session__in=sessions_pks).distinct().count(),
                    volunteers.filter(qualifs_mon1__session__in=sessions_pks).distinct().count(),
                    volunteers.filter(qualifs_actor__session__in=sessions_pks).distinct().count(),
                ])
        return dataset


class OrgaInvoicesExport(SeasonExportMixin):
    def get_dataset_title(self):
        return _('Facturation établissements dans la saison {season} {year}').format(
            season=season_verb(self.export_season),
            year=self.export_year
        )

    @property
    def export_filename(self):
        return '%s-%s-%s' % (
            _('Etablissements_Saison'),
            self.export_year,
            season_verb(self.export_season)
        )

    def get_dataset(self, html=False):
        dataset = Dataset()
        # Prépare le fichier
        dataset.append([
            u('Canton'),
            u('Établissement'),
            u('Date'),
            u('Heure'),
            u('Classe'),
            u('Participants'),
            u('Vélos loués'),
            u('Casques loués'),
        ])
        sessions = self.get_queryset()
        sessions_pks = sessions.values_list('id', flat=True)
        orgas = (
            Organization.objects.filter(sessions__in=sessions_pks)
            .order_by('address_canton', 'abbr', 'name')
            .distinct()
            .prefetch_related(
                'sessions',
                'sessions__qualifications',
            )
        )
        linktxt = '<a href="{url}">{content}</a>'
        row = []
        for orga in orgas:
            orga_row = list(row)
            orga_row.append(orga.address_canton)
            orga_row.append(orga.ifabbr if html else orga.name)
            for orga_session in sessions.filter(orga=orga):
                session_row = list(orga_row)
                session_url = reverse('session-detail',
                                      kwargs={
                                          'seasonpk': orga_session.season.pk,
                                          'pk': orga_session.id
                                          }
                                      )
                datetxt = datefilter(orga_session.day, settings.DATE_FORMAT)
                timetxt = datefilter(orga_session.begin, settings.TIME_FORMAT)
                session_row.append(mark_safe(linktxt.format(url=session_url, content=datetxt)) if html else datetxt)
                session_row.append(mark_safe(linktxt.format(url=session_url, content=timetxt)) if html else timetxt)
                for qualif in orga_session.qualifications.all():
                    qualif_row = list(session_row)
                    qualif_row.append(qualif.name)
                    qualif_row.append(qualif.n_participants)
                    qualif_row.append(qualif.n_bikes)
                    qualif_row.append(qualif.n_helmets)
                    dataset.append(qualif_row)
        return dataset


class SalariesExport(object):
    def export_month(self):
        return date(int(self.get_year()), int(self.get_month()), 1)

    def get_dataset_title(self):
        return _('Salaires - {month_year}').format(
            month_year=datefilter(self.export_month(), 'F Y')
        )

    @property
    def export_filename(self):
        return '%s-%s-%s' % (
            _('Salaires_Mois'),
            self.export_month().month,
            self.export_month().year
        )

    def get_dataset(self, html=False):
        dataset = Dataset()
        dataset.append(['test'])
        return dataset
