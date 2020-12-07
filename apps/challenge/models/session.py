# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015,2020 Didier Raboud <me+defivelo@odyx.org>
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

from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.template.defaultfilters import date
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from simple_history.models import HistoricalRecords

from apps.common.models import Address
from apps.orga.models import ORGASTATUS_ACTIVE, Organization
from apps.salary.models import Timesheet
from apps.user import FORMATION_KEYS, FORMATION_M2

from .. import (
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
    MAX_MONO1_PER_QUALI,
)

DEFAULT_SESSION_DURATION_HOURS = 3
DEFAULT_EARLY_MINUTES_FOR_HELPERS_MEETINGS = 60


class Session(Address, models.Model):
    created_on = models.DateTimeField(auto_now_add=True)

    # Time span
    day = models.DateField(_("Date"), blank=True)
    begin = models.TimeField(_("Début"), blank=True, null=True)
    duration = models.DurationField(
        _("Durée"), default=timedelta(hours=DEFAULT_SESSION_DURATION_HOURS)
    )
    visible = models.BooleanField(_("Visible pour les moniteurs"), default=False)
    orga = models.ForeignKey(
        Organization,
        verbose_name=_("Établissement"),
        related_name="sessions",
        limit_choices_to={
            "address_canton__isnull": False,
            "status__in": [ORGASTATUS_ACTIVE],
        },
        on_delete=models.CASCADE,
    )  # Don't delete orgas
    place = models.CharField(_("Lieu de la Qualif’"), max_length=512, blank=True)
    superleader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Moniteur + / Photographe"),
        related_name="sess_monplus",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    FALLBACK_CHOICES = (
        ("A", _("Programme déluge")),
        ("B", _("Annulation")),
        ("C", _("Report …")),
        ("D", _("Autre …")),
    )
    fallback_plan = models.CharField(
        _("Mauvais temps"), max_length=1, choices=FALLBACK_CHOICES, blank=True
    )
    helpers_time = models.TimeField(
        _("Heure rendez-vous moniteurs"), null=True, blank=True
    )
    helpers_place = models.CharField(
        _("Lieu rendez-vous moniteurs"), max_length=512, blank=True
    )
    apples = models.CharField(_("Pommes"), max_length=512, blank=True)
    bikes_concept = models.CharField(_("Logistique vélos"), max_length=512, blank=True)
    bikes_phone = models.CharField(_("N° de contact vélos"), max_length=13, blank=True)
    comments = models.TextField(_("Remarques"), blank=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ["day", "begin", "orga__name"]

    def get_related_timesheets(self):
        return Timesheet.objects.filter(
            (
                Q(user__qualifs_actor__in=self.qualifications.all())
                | Q(user__qualifs_mon2__in=self.qualifications.all())
                | Q(user__qualifs_mon1__in=self.qualifications.all())
            )
            & Q(date=self.day)
        ).distinct()

    def has_related_timesheets(self):
        return self.get_related_timesheets().exists()

    @cached_property
    def has_availability_incoherences(self):
        for quali in self.qualifications.all():
            if quali.has_availability_incoherences:
                return True
        return False

    @property
    def errors(self):
        errors = []
        if not self.visible:
            errors.append(_("Visibilité"))
        if not self.begin or not self.duration:
            errors.append(_("Horaire"))
        if not self.fallback_plan:
            errors.append(_("Mauvais temps"))
        if not self.apples:
            errors.append(_("Pommes"))
        if not self.bikes_concept and not self.bikes_phone:
            errors.append(_("Logistique vélos"))
        if not self.address_city:
            errors.append(_("Emplacement"))
        # Check the qualifications
        qualiq = 0
        for quali in self.qualifications.all():
            qualiq += 1
            if quali.errors:
                errors.append(_("Qualif’ {name}").format(name=quali.name))
        if qualiq == 0:
            errors.append(_("Pas de Qualifs"))
        if errors:
            return mark_safe(
                "<br />".join(
                    [
                        '<span class="btn-warning btn-xs disabled">'
                        '  <span class="glyphicon glyphicon-warning-sign"></span>'
                        "  {error}"
                        "</span>".format(error=e)
                        for e in errors
                    ]
                )
            )

    @property
    def start_datetime(self):
        return datetime.combine(
            self.day, self.begin if self.begin is not None else time.min
        )

    @property
    def end_datetime(self):
        return self.start_datetime + self.duration

    @cached_property
    def fallback(self):
        if self.fallback_plan:
            return dict(self.FALLBACK_CHOICES)[self.fallback_plan]
        return ""

    @cached_property
    def end(self):
        if self.begin and self.duration:
            day = self.day if self.day else datetime.today()
            end = datetime.combine(day, self.begin) + self.duration
            return end.time()

    @cached_property
    def chosen_staff(self):
        return (
            self.availability_statuses.exclude(
                Q(availability="n") | Q(chosen_as=CHOSEN_AS_NOT),
            )
            .prefetch_related("helper", "helper__profile", "session")
            .order_by("-chosen_as", "-availability", "-helper__profile__formation")
        )

    @cached_property
    def replacement_staff(self):
        qualifs_pks = self.qualifications.values_list("id", flat=True)
        return (
            self.chosen_staff.filter(chosen_as=CHOSEN_AS_REPLACEMENT)
            .exclude(helper__qualifs_mon1__in=qualifs_pks)
            .exclude(helper__qualifs_mon2__in=qualifs_pks)
            .exclude(helper__qualifs_actor__in=qualifs_pks)
        )

    @cached_property
    def n_qualifications(self):
        return self.qualifications.count()

    def chosen_helpers(self):
        return self.chosen_staff.filter(
            chosen_as__in=[CHOSEN_AS_HELPER, CHOSEN_AS_LEADER],
            helper__profile__formation__in=FORMATION_KEYS,
        ).order_by(
            "-helper__profile__formation", "helper__first_name", "helper__last_name"
        )

    def chosen_helpers_M2(self):
        return self.chosen_helpers().filter(helper__profile__formation=FORMATION_M2)

    def helper_needs(self):
        # Struct with 0:0, 1:needs in helper_formation 1, same for 2
        n_sessions = self.n_qualifications
        return [0] + [n_sessions * (MAX_MONO1_PER_QUALI), n_sessions]

    def chosen_actors(self):
        return self.chosen_staff.filter(chosen_as=CHOSEN_AS_ACTOR).exclude(
            helper__profile__actor_for__isnull=True
        )

    def actor_needs(self):
        return self.n_qualifications

    def user_assignment(self, user):
        # Check as what a user is assigned to that session
        for q in self.qualifications.all():
            if user == q.leader:
                return CHOSEN_AS_LEADER
            if user in q.helpers.all():
                return CHOSEN_AS_HELPER
            if user == q.actor:
                return CHOSEN_AS_ACTOR
        return None

    def n_quali_things(self, field):
        return sum([q for q in self.qualifications.values_list(field, flat=True) if q])

    @cached_property
    def n_bikes(self):
        return self.n_quali_things("n_bikes")

    @cached_property
    def n_helmets(self):
        return self.n_quali_things("n_helmets")

    @cached_property
    def n_participants(self):
        return self.n_quali_things("n_participants")

    def helpers_time_with_default(self):
        if self.helpers_time:
            return self.helpers_time
        if self.begin:
            # Compute a default value with regards to the start time
            helpers_time = date(
                (
                    datetime.combine(datetime.today(), self.begin)
                    - timedelta(minutes=DEFAULT_EARLY_MINUTES_FOR_HELPERS_MEETINGS)
                ).time(),
                settings.TIME_FORMAT,
            )
            return mark_safe("<em>{}</em>".format(helpers_time))
        return ""

    @cached_property
    def city(self):
        if self.address_city:
            return self.address_city
        elif self.orga.address_city:
            return self.orga.address_city

    @cached_property
    def season(self):
        from .season import Season

        season = Season.objects.filter(
            year=self.day.year,
            month_start__lte=self.day.month,
            n_months__gt=self.day.month - F("month_start"),
            cantons__contains=self.orga.address_canton,
        ).first()

        if season:
            return season

        # Should only rarely happen, so afford an other request; look for Season objects in the past year, spanning to ours.
        for offset in [1, 2]:
            seasons = Season.objects.filter(
                year=self.day.year - offset,
                cantons__contains=self.orga.address_canton,
            )
            for s in seasons.all():
                if s.begin <= self.day <= s.end:
                    return s

    @cached_property
    def short(self):
        return _("{place} {date}{time}").format(
            date=date(self.day, settings.DATE_FORMAT_SHORT),
            time=(
                "@" + date(self.begin, settings.TIME_FORMAT_SHORT) if self.begin else ""
            ),
            place=self.orga.name,
        )

    def __str__(self):
        return (
            date(self.day, settings.DATE_FORMAT)
            + (" (%s)" % date(self.begin, settings.TIME_FORMAT) if self.begin else "")
            + (
                " - %s" % (self.orga.abbr if self.orga.abbr else self.orga.name)
                if self.orga
                else ""
            )
            + (
                " - %s"
                % (
                    self.address_city
                    if self.address_city
                    else (
                        self.orga.address_city
                        if (self.orga and self.orga.address_city)
                        else ""
                    )
                )
            )
        )
