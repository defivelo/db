# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2020 Sylvain Fankhauser <sylvain.fankhauser@liip.ch>
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

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext as u
from django.utils.translation import ugettext_lazy as _

from apps.challenge.models import Season, Session
from apps.orga.models import Organization


class Invoice(models.Model):
    STATUS_DRAFT = 0
    STATUS_VALIDATED = 1
    STATUS_CHOICES = (
        (STATUS_DRAFT, _("Brouillon")),
        (STATUS_VALIDATED, _("Validée")),
    )

    generated_at = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_DRAFT)
    ref = models.CharField(_("Référence"), max_length=20, blank=False, unique=True)
    title = models.CharField(_("Titre"), max_length=255, blank=True)
    organization = models.ForeignKey(
        Organization, verbose_name=_("Établissement"), on_delete=models.PROTECT
    )
    season = models.ForeignKey(
        Season, verbose_name=_("Saison"), on_delete=models.PROTECT
    )

    def __str__(self):
        return u(f"Facture {self.ref} pour {self.organization} / {self.season}")

    def get_absolute_url(self):
        return reverse_lazy(
            "invoice-detail",
            kwargs={
                "seasonpk": self.season.pk,
                "orgapk": self.organization.pk,
                "invoiceref": self.ref,
            },
        )

    @property
    def sessions(self):
        return self.season.sessions.filter(orga=self.organization)

    def sum_of(self, thing: str):
        return self.lines.aggregate(total=Sum(thing))["total"]

    def sum_of_2(self, thing_1: str, thing_2: str):
        return self.lines.aggregate(total=Sum(F(thing_1) + F(thing_2)))["total"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate sum_* methods
        for thing in ["nb_bikes", "nb_participants", "cost_bikes", "cost_participants"]:
            setattr(self, f"sum_{thing}", self.sum_of(thing=thing))
        # Generate sum_* methods
        for prefix in ["nb", "cost"]:
            setattr(
                self,
                f"sum_{prefix}",
                self.sum_of_2(
                    thing_1=f"{prefix}_bikes", thing_2=f"{prefix}_participants"
                ),
            )

    @cached_property
    def status_full(self):
        try:
            return dict(self.STATUS_CHOICES)[self.status]
        except KeyError:
            return ""

    @property
    def is_locked(self):
        return self.status == self.STATUS_VALIDATED

    @property
    def status_class(self):
        css_class = "default"
        if self.status == self.STATUS_DRAFT:
            css_class = "warning"  # Orange
        elif self.status == self.STATUS_VALIDATED:
            css_class = "success"  # Green
        return css_class


class InvoiceLine(models.Model):
    session = models.ForeignKey(Session, on_delete=models.PROTECT)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    nb_bikes = models.PositiveSmallIntegerField()
    nb_participants = models.PositiveSmallIntegerField()
    cost_bikes = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0)],
    )
    cost_participants = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0)],
    )

    class Meta:
        unique_together = (("session", "invoice"),)

    def __str__(self):
        return u(
            f"{self.invoice.ref}: {self.session} - Vélos: {self.nb_bikes} ({self.cost_bikes} CHF) - Participants: {self.nb_participants} ({self.cost_participants} CHF)"
        )

    def cost(self):
        return self.cost_bikes + self.cost_participants
