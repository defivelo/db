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
from apps.user import FORMATION_M1, FORMATION_M2, formation_short
from defivelo.roles import user_cantons
from defivelo.templatetags.dv_filters import canton_abbr_short, season_verb

linktxt = '<a href="{url}">{content}</a>'


class SeasonSessionsMixin(object):
    limit_to_my_cantons = True

    def get_queryset(self):
        begin = date(self.export_year, 1, 1)
        if self.export_season == DV_SEASON_AUTUMN:
            begin = date(self.export_year, DV_SEASON_LAST_SPRING_MONTH + 1, 1)
        end = date(self.export_year, DV_SEASON_LAST_SPRING_MONTH + 1, 1) - timedelta(days=1)
        if self.export_season == DV_SEASON_AUTUMN:
            end = date(self.export_year, 12, 31)
        sessions = (
            Session.objects
            .filter(
                day__gte=begin, day__lte=end,
            )
            .order_by('day', 'begin')
            .prefetch_related('orga')
        )
        if self.limit_to_my_cantons:
            sessions = sessions.filter(
                orga__address_canton__in=user_cantons(self.request.user)
            )
        return sessions


class SeasonStatsExport(SeasonSessionsMixin):
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


class OrgaInvoicesExport(SeasonSessionsMixin):
    # Saison par canton puis qualif par établissement
    canton_orga_not_sessions = True

    def get_dataset_title(self):
        return '{title} - {season} {year}'.format(
            title=(
                u('Facturation établissements dans la saison')
                if self.canton_orga_not_sessions
                else u('Planification logistique')
            ),
            season=season_verb(self.export_season),
            year=self.export_year
        )

    @property
    def export_filename(self):
        return '%s-%s-%s-%s' % (
            u('Établissements') if self.canton_orga_not_sessions else u('Logistique'),
            u('Saison'),
            self.export_year,
            season_verb(self.export_season)
        )

    def get_dataset(self, html=False):
        dataset = Dataset()
        # Prépare le fichier
        row = [
            u('Canton'),
            u('Établissement'),
        ]
        if not self.canton_orga_not_sessions:
            row = row + [u('Lieu')]
        row = row + [
            u('Date'),
            u('Heure'),
            u('Classe') if self.canton_orga_not_sessions else u('Classes'),
            u('Participants'),
            u('Vélos loués'),
            u('Casques loués'),
        ]
        if not self.canton_orga_not_sessions:
            row = row + [
                u('Logistique vélos'),
                u('N° de contact vélos')
            ]
        dataset.append(row)
        sessions = self.get_queryset()
        if not self.canton_orga_not_sessions:
            sessions = sessions.annotate(
                n_qualifs=Count('qualifications'),
                n_participants=Sum('qualifications__n_participants'),
                n_bikes=Sum('qualifications__n_bikes'),
                n_helmets=Sum('qualifications__n_helmets'),
            )
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
        row = []
        if self.canton_orga_not_sessions:
            for orga in orgas:
                orga_row = list(row)
                orga_row.append(orga.address_canton)
                orga_row.append(orga.ifabbr if html else orga.name)
                for orga_session in sessions.filter(orga=orga):
                    session_row = list(orga_row)
                    season = orga_session.season
                    url = None
                    if season and html:
                        url = reverse('session-detail',
                                      kwargs={
                                          'seasonpk': season.pk,
                                          'pk': orga_session.id
                                          }
                                      )
                    datetxt = datefilter(orga_session.day, settings.DATE_FORMAT_COMPACT)
                    timetxt = datefilter(orga_session.begin, settings.TIME_FORMAT_SHORT)
                    session_row.append(mark_safe(linktxt.format(url=url, content=datetxt)) if url else datetxt)
                    session_row.append(mark_safe(linktxt.format(url=url, content=timetxt)) if url else timetxt)
                    for qualif in orga_session.qualifications.all():
                        qualif_row = list(session_row)
                        qualif_row.append(qualif.name)
                        qualif_row.append(qualif.n_participants)
                        qualif_row.append(qualif.n_bikes)
                        qualif_row.append(qualif.n_helmets)
                        dataset.append(qualif_row)
        else:
            for session in sessions:
                season = session.season
                url = None
                if season and html:
                    url = reverse('session-detail',
                                  kwargs={
                                      'seasonpk': season.pk,
                                      'pk': session.id
                                      }
                                  )
                datetxt = datefilter(session.day, settings.DATE_FORMAT_COMPACT)
                timetxt = datefilter(session.begin, settings.TIME_FORMAT_SHORT)
                dataset.append([
                    session.orga.address_canton,
                    session.orga.ifabbr if html else session.orga.name,
                    session.city,
                    mark_safe(linktxt.format(url=url, content=datetxt)) if url else datetxt,
                    mark_safe(linktxt.format(url=url, content=timetxt)) if url else timetxt,
                    session.n_qualifs,
                    session.n_participants,
                    session.n_bikes,
                    session.n_helmets,
                    session.bikes_concept,
                    session.bikes_phone,
                ])
        return dataset


class SalariesExport(object):
    # Seulement les _salaires_ (moniteurs)
    salaries_not_expenses = True

    def export_month(self):
        return date(int(self.get_year()), int(self.get_month()), 1)

    def get_dataset_title(self):
        return '{title} - {date}'.format(
            title=u('Salaires') if self.salaries_not_expenses else u('Défraiements'),
            date=datefilter(self.export_month(), 'F Y')
        )

    @property
    def export_filename(self):
        return '%s-%s-%s-%s' % (
            u('Salaires') if self.salaries_not_expenses else u('Défraiements'),
            u('Mois'),
            self.export_month().month,
            self.export_month().year
        )

    def get_dataset(self, html=False):
        dataset = Dataset()
        # Cases en haut à gauche
        session_cols = ['' for i in range(2)]
        def bolden(s):
            return mark_safe('<b>%s</b>' % s) if html else s

        dataset.append_col(session_cols + [bolden(u('Nom'))])
        dataset.append_col(session_cols + [bolden(u('Adresse'))])
        dataset.append_col(session_cols + [bolden(u('NPA'))])
        dataset.append_col(session_cols + [bolden(u('Ville'))])
        dataset.append_col(session_cols + [bolden(u('N° AVS'))])
        dataset.append_col(session_cols + [bolden(u('IBAN'))])
        dataset.append_col(session_cols + [bolden(u('Canton d\'affiliation'))])

        for session in self.object_list:
            orga = session.orga.ifabbr if html else session.orga.name
            season = session.season
            link = None
            if season and html:
                link = mark_safe(
                    linktxt.format(
                        url=reverse('session-detail',
                                    kwargs={
                                        'seasonpk': season.pk,
                                        'pk': session.pk
                                        }),
                        content=orga))
            dataset.append_col([
                link if link else orga,
                bolden(datefilter(session.day, 'j.m')),
                bolden(datefilter(session.begin, settings.TIME_FORMAT))
            ])
        sessions_pks = self.object_list.values_list('id', flat=True)
        everyone = get_user_model().objects
        if self.salaries_not_expenses:
            # All helpers in these sessions
            everyone = everyone.filter(
                Q(qualifs_mon1__session__in=sessions_pks) |
                Q(qualifs_mon2__session__in=sessions_pks)
            )
        else:
            # All actors in these sessions
            everyone = everyone.filter(qualifs_actor__session__in=sessions_pks)
        everyone = (
            everyone
            .filter(profile__affiliation_canton__in=user_cantons(self.request.user))
            .prefetch_related('profile')
            .order_by('profile__affiliation_canton', 'last_name')
            .distinct()
        )
        for user in everyone:
            fullname = user.get_full_name()
            url = reverse('user-detail', kwargs={'pk': user.pk})
            row = [
                mark_safe(linktxt.format(url=url, content=fullname)) if html else fullname,
                '%s %s' % (user.profile.address_street, user.profile.address_no),
                user.profile.address_zip,
                user.profile.address_city,
                (
                    (user.profile.social_security[:5] + '…' if len(user.profile.social_security) > 0 else '')
                    if html else user.profile.social_security
                ),
                (
                    (user.profile.iban[:5] + '…' if len(user.profile.iban) > 0 else '')
                    if html else user.profile.iban_nice
                ),
                canton_abbr_short(user.profile.affiliation_canton, abbr=False),
            ]
            for session in self.object_list:
                label = ''
                for quali in session.qualifications.all():
                    if self.salaries_not_expenses:
                        if user.id == quali.leader_id:
                            label = formation_short(FORMATION_M2, True)
                            break
                        elif user in quali.helpers.all():
                            label = formation_short(FORMATION_M1, True)
                            break
                    elif user.id == quali.actor_id:
                        label = u('Int.')
                        break
                row.append(label)
            dataset.append(row)
        return dataset


class ExpensesExport(SalariesExport):
    # Seulement les _défraiments_ (intervenants)
    salaries_not_expenses = False


class LogisticsExport(OrgaInvoicesExport):
    # Saison dans l'ordre avec les besoins de vélos, pas par Qualif'
    canton_orga_not_sessions = False
