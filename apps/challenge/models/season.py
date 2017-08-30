# -*- coding: utf-8 -*-
#
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
from __future__ import unicode_literals

from datetime import date, timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField

from apps.common import (
    DV_SEASON_AUTUMN, DV_SEASON_CHOICES, DV_SEASON_LAST_SPRING_MONTH, DV_SEASON_SPRING, DV_STATE_CHOICES,
)

from .session import Session


@python_2_unicode_compatible
class Season(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    year = models.PositiveSmallIntegerField(_('Année'))
    season = models.PositiveSmallIntegerField(_('Saison'),
                                              choices=DV_SEASON_CHOICES,
                                              default=DV_SEASON_SPRING)
    cantons = MultiSelectField(_('Cantons'), choices=sorted(DV_STATE_CHOICES))
    leader = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('Chargé de projet'),
                               limit_choices_to={
                                   'managedstates__isnull': False
                               },
                               on_delete=models.CASCADE
                               )

    class Meta:
        verbose_name = _('Saison')
        verbose_name_plural = _('Saisons')
        ordering = ['year', 'season', ]

    @cached_property
    def cantons_verb(self):
        if self.cantons:
            return [c[1] for c in DV_STATE_CHOICES if c[0] in self.cantons]

    @cached_property
    def begin(self):
        if self.season == DV_SEASON_SPRING:
            return date(self.year, 1, 1)
        if self.season == DV_SEASON_AUTUMN:
            return date(self.year, DV_SEASON_LAST_SPRING_MONTH + 1, 1)

    @cached_property
    def end(self):
        if self.season == DV_SEASON_SPRING:
            return date(self.year, DV_SEASON_LAST_SPRING_MONTH + 1, 1) - timedelta(days=1)
        if self.season == DV_SEASON_AUTUMN:
            return date(self.year, 12, 31)

    @cached_property
    def season_full(self):
        return dict(DV_SEASON_CHOICES)[self.season]

    @property
    def sessions(self):
        return Session.objects.filter(
            orga__address_canton__in=self.cantons,
            day__gte=self.begin,
            day__lte=self.end
            ).prefetch_related(
                'qualifications',
                'qualifications__activity_A',
                'qualifications__activity_B',
                'qualifications__activity_C',
                'qualifications__leader',
                'qualifications__helpers',
                'qualifications__actor',
                'orga'
            )

    @property
    def sessions_with_qualifs(self):
        if not hasattr(self, 'sessions_with_q'):
            self.sessions_with_q = \
                self.sessions.prefetch_related(
                    'availability_statuses'
                ).annotate(
                    models.Count('qualifications')
                ).filter(qualifications__count__gt=0, )
        return self.sessions_with_q

    def get_absolute_url(self):
        return reverse('season-detail', args=[self.pk])

    @cached_property
    def moment(self):
        return _('{saison} {annee}').format(
            saison=self.season_full,
            annee=self.year,
            )

    @cached_property
    def desc(self):
        return _('{cantons} - {moment}').format(
            moment=self.moment,
            cantons=", ".join(self.cantons),
            )

    def __str__(self):
        return (
            self.desc +
            (" - " + self.leader.get_full_name() if self.leader else '')
        )
