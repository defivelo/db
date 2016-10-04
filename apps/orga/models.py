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


@python_2_unicode_compatible
class Organization(Address, models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    name = models.CharField(_('Nom'), max_length=255)

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
