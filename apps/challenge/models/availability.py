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
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from .. import CHOICE_CHOICES, CHOSEN_AS_NOT
from .session import Session


@python_2_unicode_compatible
class HelperSessionAvailability(models.Model):
    AVAILABILITY_CHOICES = (
        ('y', _('Oui')),
        ('i', _('Si nécessaire')),
        ('n', _('Non')),
    )
    created_on = models.DateTimeField(auto_now_add=True)
    session = models.ForeignKey(Session, verbose_name=_('Session'),
                                related_name='availability_statuses',
                                on_delete=models.CASCADE)
    helper = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('Moniteur'),
                               related_name='availabilities',
                               limit_choices_to={'profile__isnull': False},
                               on_delete=models.CASCADE)
    availability = models.CharField(_("Disponible"), max_length=1,
                                    choices=AVAILABILITY_CHOICES)
    chosen_as = models.PositiveSmallIntegerField(
        _("Sélectionné pour la session comme"),
        choices=CHOICE_CHOICES, default=CHOSEN_AS_NOT)

    @cached_property
    def chosen(self):
        return self.chosen_as != CHOSEN_AS_NOT

    class Meta:
        verbose_name = _('Disponibilité par session')
        verbose_name_plural = _('Disponibilités par session')
        ordering = ['session', 'helper', 'availability']
        unique_together = (('session', 'helper', ), )

    def __str__(self):
        is_available = _("n'est pas disponible")
        if self.availability == 'y':
            is_available = _('est disponible')
        elif self.availability == 'i':
            is_available = _('est disponible si nécessaire')

        return _('{session}: {chosen}{helper} {is_available}').format(
             session=self.session,
             chosen="(%s) " % self.chosen_as if self.chosen else '',
             helper=self.helper.get_full_name(),
             is_available=is_available)
