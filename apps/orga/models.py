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
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from apps.common import STDGLYPHICON
from apps.common.models import Address

ORGASTATUS_UNDEF = 0
ORGASTATUS_ACTIVE = 10
ORGASTATUS_INACTIVE = 30

ORGASTATUS_CHOICES = (
    (ORGASTATUS_UNDEF, "---------"),
    (ORGASTATUS_ACTIVE, _("Actif")),
    (ORGASTATUS_INACTIVE, _("Inactif")),
)


@python_2_unicode_compatible
class Organization(Address, models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    abbr = models.CharField(_("Abréviation"), max_length=16, blank=True)
    name = models.CharField(_("Nom"), max_length=255)
    website = models.URLField(_("Site web"), blank=True)
    status = models.PositiveSmallIntegerField(
        _("Statut"), choices=ORGASTATUS_CHOICES, default=ORGASTATUS_ACTIVE
    )
    comments = models.TextField(_("Remarques"), blank=True)

    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="managed_organizations",
        verbose_name=_("Coordinateur"),
        null=True,
        on_delete=models.SET_NULL,
    )

    @cached_property
    def abbr_verb(self):
        return mark_safe(
            '<abbr title="{name}">{abbr}</abbr>'.format(name=self.name, abbr=self.abbr)
        )

    @cached_property
    def ifabbr(self):
        return self.abbr_verb if self.abbr else self.name

    @cached_property
    def status_full(self):
        if self.status:
            return dict(ORGASTATUS_CHOICES)[self.status]
        return ""

    def status_icon(self):
        icon = ""
        title = self.status_full
        if self.status == ORGASTATUS_ACTIVE:
            icon = "star"
        elif self.status == ORGASTATUS_INACTIVE:
            icon = "hourglass"
        if icon:
            return mark_safe(STDGLYPHICON.format(icon=icon, title=title))
        return ""

    def status_class(self):
        css_class = "default"
        if self.status == ORGASTATUS_ACTIVE:
            css_class = "success"  # Green
        elif self.status == ORGASTATUS_INACTIVE:
            css_class = "danger"  # Red
        return css_class

    def shortname(self):
        return "{abbr}{city}".format(
            abbr=self.ifabbr,
            city=" (%s)" % self.address_city if self.address_city else "",
        )

    class Meta:
        verbose_name = _("Établissement")
        verbose_name_plural = _("Établissements")
        ordering = ["name"]

    def __str__(self):
        return "{name}{city}".format(
            name=self.name,
            city=" (%s)" % self.address_city if self.address_city else "",
        )

    def get_absolute_url(self):
        return reverse("organization-detail", args=[self.pk])
