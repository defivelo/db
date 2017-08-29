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

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from apps.common.models import Address

ORGASTATUS_UNDEF = 0
ORGASTATUS_ACTIVE = 10
ORGASTATUS_INACTIVE = 30

ORGASTATUS_CHOICES = (
    (ORGASTATUS_UNDEF, '---------'),
    (ORGASTATUS_ACTIVE, _('Actif')),
    (ORGASTATUS_INACTIVE, _('Inactif')),
)


@python_2_unicode_compatible
class Organization(Address, models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    abbr = models.CharField(_('Abbréviation'), max_length=16, blank=True)
    name = models.CharField(_('Nom'), max_length=255)
    website = models.URLField(_('Site web'), blank=True)
    coordinator_fullname = models.CharField(_('Coordinateur'),
                                            max_length=512, blank=True)
    coordinator_phone = models.CharField(_('Téléphone'),
                                         max_length=13, blank=True)
    coordinator_natel = models.CharField(_('Natel'),
                                         max_length=13, blank=True)
    coordinator_email = models.EmailField(_('Courriel'),
                                          blank=True)
    status = models.PositiveSmallIntegerField(
        _("Statut"),
        choices=ORGASTATUS_CHOICES,
        default=ORGASTATUS_ACTIVE)
    comments = models.TextField(_('Remarques'), blank=True)

    @property
    def mailtolink(self):
        return (
            '{name} <{email}>'.format(
                name=self.coordinator_fullname,
                email=self.coordinator_email)
            )

    class Meta:
        verbose_name = _('Établissement')
        verbose_name_plural = _('Établissements')
        ordering = ['name']

    def __str__(self):
        return "{name}{city}".format(
            name=self.name,
            city=' (%s)' % self.address_city if self.address_city else '')

    def get_absolute_url(self):
        return reverse('organization-detail', args=[self.pk])
