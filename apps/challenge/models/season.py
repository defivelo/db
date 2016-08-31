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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import date
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from localflavor.ch.ch_states import STATE_CHOICES
from multiselectfield import MultiSelectField

from .session import Session


@python_2_unicode_compatible
class Season(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    begin = models.DateField(_('Début'))
    end = models.DateField(_('Fin'))
    cantons = MultiSelectField(_('Cantons'), choices=STATE_CHOICES)
    leader = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('Chargé de projet'),
                               blank=True, null=True)

    class Meta:
        verbose_name = _('Saison')
        verbose_name_plural = _('Saisons')
        ordering = ['begin', 'end', ]

    @property
    def cantons_verb(self):
        if self.cantons:
            return [c[1] for c in STATE_CHOICES if c[0] in self.cantons]

    @property
    def sessions(self):
        return Session.objects.filter(
            organization__address_canton__in=self.cantons,
            day__gte=self.begin,
            day__lt=self.end
            )

    @property
    def sessions_with_qualifs(self):
        if not hasattr(self, 'sessions_with_q'):
            self.sessions_with_q = self.sessions.annotate(models.Count('qualifications')).filter(
                qualifications__count__gt=0,
                )
        return self.sessions_with_q

    def get_absolute_url(self):
        return reverse('season-detail', args=[self.pk])

    def desc(self):
        return _('{depuis_mois} à {jusqu_mois} ({cantons})').format(
            depuis_mois=date(self.begin, "F").title(),
            jusqu_mois=date(self.end, "F Y"),
            cantons=", ".join(self.cantons),
            )

    def __str__(self):
        return (
            self.desc() +
            (" - " + self.leader.get_full_name() if self.leader else '')
        )
