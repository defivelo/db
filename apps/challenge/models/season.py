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
from django.db import models
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from multiselectfield import MultiSelectField
from simple_history.models import HistoricalRecords

from apps.common import (
    DV_SEASON_AUTUMN,
    DV_SEASON_CHOICES,
    DV_SEASON_LAST_SPRING_MONTH,
    DV_SEASON_SPRING,
    DV_SEASON_STATE_ARCHIVED,
    DV_SEASON_STATE_FINISHED,
    DV_SEASON_STATE_OPEN,
    DV_SEASON_STATE_PLANNING,
    DV_SEASON_STATE_RUNNING,
    DV_SEASON_STATES,
    DV_STATE_CHOICES,
    STDGLYPHICON,
)
from defivelo.templatetags.dv_filters import cantons_abbr


@python_2_unicode_compatible
class Season(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    year = models.PositiveSmallIntegerField(_("Année"))
    season = models.PositiveSmallIntegerField(
        _("Saison"), choices=DV_SEASON_CHOICES, default=DV_SEASON_SPRING
    )
    cantons = MultiSelectField(_("Cantons"), choices=sorted(DV_STATE_CHOICES))
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Chargé de projet"),
        limit_choices_to={"managedstates__isnull": False},
        on_delete=models.CASCADE,
    )
    state = models.PositiveSmallIntegerField(
        _("État"), choices=DV_SEASON_STATES, default=DV_SEASON_STATE_PLANNING
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Saison")
        verbose_name_plural = _("Saisons")
        ordering = [
            "year",
            "-season",
            "cantons",
        ]

    @cached_property
    def begin(self):
        if self.season == DV_SEASON_SPRING:
            return date(self.year, 1, 1)
        if self.season == DV_SEASON_AUTUMN:
            return date(self.year, DV_SEASON_LAST_SPRING_MONTH + 1, 1)

    @cached_property
    def end(self):
        if self.season == DV_SEASON_SPRING:
            return date(self.year, DV_SEASON_LAST_SPRING_MONTH + 1, 1) - timedelta(
                days=1
            )
        if self.season == DV_SEASON_AUTUMN:
            return date(self.year, 12, 31)

    @cached_property
    def state_full(self):
        return dict(DV_SEASON_STATES)[self.state]

    @cached_property
    def state_icon(self):
        icon = ""
        title = self.state_full
        if self.state == DV_SEASON_STATE_PLANNING:
            icon = "calendar"
        elif self.state == DV_SEASON_STATE_OPEN:
            icon = "flash"
        elif self.state == DV_SEASON_STATE_RUNNING:
            icon = "apple"
        elif self.state == DV_SEASON_STATE_FINISHED:
            icon = "floppy-saved"
        elif self.state == DV_SEASON_STATE_ARCHIVED:
            icon = "folder-close"
        if icon:
            return mark_safe(STDGLYPHICON.format(icon=icon, title=title))
        return ""

    @cached_property
    def state_class(self):
        css_class = "default"
        if self.state == DV_SEASON_STATE_PLANNING:
            css_class = "warning"  # Orange
        elif self.state == DV_SEASON_STATE_OPEN:
            css_class = "success"  # Green
        elif self.state == DV_SEASON_STATE_RUNNING:
            css_class = "warning"  # Orange
        elif self.state == DV_SEASON_STATE_FINISHED:
            css_class = "default disabled"  # Black
        elif self.state == DV_SEASON_STATE_ARCHIVED:
            css_class = "default disabled"  # Black
        return css_class

    @cached_property
    def staff_can_update_availability(self):
        return self.state == DV_SEASON_STATE_OPEN

    @cached_property
    def staff_can_see_planning(self):
        return self.state == DV_SEASON_STATE_RUNNING

    @property
    def can_set_state_open(self):
        return self.state == DV_SEASON_STATE_PLANNING

    @property
    def can_set_state_running(self):
        return self.state in [DV_SEASON_STATE_OPEN]

    @cached_property
    def manager_can_crud(self):
        return self.state != DV_SEASON_STATE_ARCHIVED

    @cached_property
    def season_full(self):
        return dict(DV_SEASON_CHOICES)[self.season]

    @property
    def has_availability_incoherences(self):
        for session in self.sessions_with_qualifs:
            if session.has_availability_incoherences:
                return True
        return False

    @property
    def sessions(self):
        from .session import Session

        return Session.objects.filter(
            orga__address_canton__in=self.cantons,
            day__gte=self.begin,
            day__lte=self.end,
        ).prefetch_related(
            "qualifications",
            "qualifications__activity_A",
            "qualifications__activity_B",
            "qualifications__activity_C",
            "qualifications__leader",
            "qualifications__helpers",
            "qualifications__actor",
            "orga",
        )

    @property
    def sessions_by_orga(self):
        return self.sessions.order_by("orga__name", "day", "begin")

    @cached_property
    def sessions_with_qualifs(self):
        if not hasattr(self, "sessions_with_q"):
            self.sessions_with_q = (
                self.sessions.prefetch_related("availability_statuses")
                .annotate(models.Count("qualifications"))
                .filter(qualifications__count__gt=0)
                .order_by("day", "begin", "orga__name")
            )
        return self.sessions_with_q

    def get_absolute_url(self):
        return reverse("season-detail", args=[self.pk])

    @cached_property
    def moment(self):
        return _("{saison} {annee}").format(saison=self.season_full, annee=self.year,)

    def save(self, *args, **kwargs):
        """
        Override save to clear some cached properties
        """
        super().save(*args, **kwargs)
        # Clear cached properties
        for cached_prop in [
            "can_set_state_running",
            "staff_can_update_availability",
            "staff_can_see_planning",
            "manager_can_crud",
            "season_full",
        ]:
            try:
                del self.__dict__[cached_prop]
            except KeyError:
                pass

    def desc(self, abbr=False):
        return mark_safe(
            _("{cantons} - {moment}").format(
                moment=self.moment, cantons=", ".join(cantons_abbr(self.cantons, abbr)),
            )
        )

    @cached_property
    def desc_abbr(self):
        return self.desc(True)

    def __str__(self):
        return "{desc}{leader}".format(
            desc=self.desc(False),
            leader=" - %s" % self.leader.get_full_name() if self.leader else "",
        )
