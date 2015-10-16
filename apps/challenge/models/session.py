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

from datetime import datetime, timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q, Sum
from django.template.defaultfilters import date
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from apps.common.models import Address
from apps.orga.models import Organization

from .. import MAX_MONO1_PER_QUALI

DEFAULT_SESSION_DURATION_HOURS = 3
DEFAULT_EARLY_MINUTES_FOR_HELPERS_MEETINGS = 60


@python_2_unicode_compatible
class Session(Address, models.Model):
    created_on = models.DateTimeField(auto_now_add=True)

    # Time span
    day = models.DateField(_('Date'), blank=True)
    begin = models.TimeField(_('Début'), blank=True, null=True)
    duration = models.DurationField(_('Durée'),
                                    default=timedelta(
                                        hours=DEFAULT_SESSION_DURATION_HOURS
                                        ))
    organization = models.ForeignKey(Organization,
                                     verbose_name=_('Établissement'),
                                     related_name='sessions',
                                     blank=True, null=True)
    FALLBACK_CHOICES = (
        ('A', _('Programme déluge')),
        ('B', _('Annulation')),
        ('C', _('Report …')),
        ('D', _('Autre …')),
    )
    fallback_plan = models.CharField(_("Mauvais temps"), max_length=1,
                                     choices=FALLBACK_CHOICES, blank=True)
    helpers_time = models.TimeField(_('Heure rendez-vous moniteurs'),
                                    null=True, blank=True)
    helpers_place = models.CharField(_("Lieu rendez-vous moniteurs"),
                                     max_length=512, blank=True)
    apples = models.CharField(_("Pommes"), max_length=512, blank=True)
    comments = models.TextField(_('Remarques'), blank=True)

    class Meta:
        verbose_name = _('Session')
        verbose_name_plural = _('Sessions')
        unique_together = (('organization', 'begin', 'day'),)
        ordering = ['day', 'begin', 'organization__name']

    @property
    def errors(self):
        errors = []
        if not self.begin or not self.duration:
            errors.append(_('Horaire'))
        if not self.fallback_plan:
            errors.append(_('Mauvais temps'))
        if not self.apples:
            errors.append(_('Pommes'))
        # Check the qualifications
        qualiq = 0
        for quali in self.qualifications.all():
            qualiq += 1
            if quali.errors:
                errors.append(_('Quali : {name}').format(name=quali.name))
        if qualiq == 0:
            errors.append(_('Pas de qualifications'))
        if errors:
            return mark_safe(
                '<br />'.join(
                    [
                        '<span class="btn-warning btn-xs disabled">'
                        '  <span class="glyphicon glyphicon-warning-sign"></span>'
                        '  {error}'
                        '</span>'.format(error=e) for e in errors
                    ])
                )

    @cached_property
    def fallback(self):
        if self.fallback_plan:
            return dict(self.FALLBACK_CHOICES)[self.fallback_plan]
        return ''

    @cached_property
    def end(self):
        if self.begin and self.duration:
            day = self.day if self.day else datetime.today()
            end = datetime.combine(day, self.begin) + self.duration
            return end.time()

    @cached_property
    def chosen_staff(self):
        return (
            self.availability_statuses
            .filter(chosen=True)
            .exclude(availability='n')
            .order_by('-availability')
        )

    @cached_property
    def n_qualifications(self):
        return self.qualifications.count()

    def chosen_helpers(self):
        return (
            self.chosen_staff
            .filter(helper__profile__formation__in=['M1', 'M2'])
            .order_by('-helper__profile__formation',
                      'helper__first_name',
                      'helper__last_name')
        )

    def chosen_helpers_M2(self):
        return self.chosen_helpers().filter(helper__profile__formation='M2')

    def helper_needs(self):
        # Struct with 0:0, 1:needs in helper_formation 1, same for 2
        n_sessions = self.n_qualifications
        return [0] + [n_sessions * (MAX_MONO1_PER_QUALI + 1), n_sessions]

    def chosen_actors(self):
        return self.chosen_staff.exclude(
            helper__profile__actor_for__isnull=True
        )

    def actor_needs(self):
        return self.n_qualifications

    def has_user_assigned(self, user):
        # Check if a given user is assigned to that session
        return (
            self.qualifications.filter(
                Q(leader=user) | Q(helpers=user) | Q(actor=user)
            ).exists()
        )

    def n_quali_things(self, field):
        return sum(
            [q for q in self.qualifications.values_list(field, flat=True)]
        )

    @cached_property
    def n_bikes(self):
        return self.n_quali_things('n_bikes')

    @cached_property
    def n_helmets(self):
        return self.n_quali_things('n_helmets')

    def helpers_time_with_default(self):
        if self.helpers_time:
            return self.helpers_time
        if self.begin:
            # Compute a default value with regards to the start time
            helpers_time = date((
                datetime.combine(datetime.today(), self.begin) -
                timedelta(minutes=DEFAULT_EARLY_MINUTES_FOR_HELPERS_MEETINGS)
                ).time(), settings.TIME_FORMAT)
            return mark_safe('<em>{}</em>'.format(helpers_time))
        return ''

    def __str__(self):
        return (
            date(self.day, settings.DATE_FORMAT) +
            (' (%s)' % date(self.begin, settings.TIME_FORMAT) if self.begin else '') +
            (' - %s' % self.organization.name if self.organization else '') +
            (' (%s)' % (self.address_city if self.address_city else (self.organization.address_city if (self.organization and self.organization.address_city) else '')))
            )
