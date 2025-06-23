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
from decimal import ROUND_HALF_EVEN
from decimal import Decimal as D
from typing import Iterable

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy as _p

from simple_history.utils import get_history_manager_for_model

from apps.orga.models import Organization

from .season import Season
from .session import Session
from .settings import AnnualStateSetting

HistoricalSession = get_history_manager_for_model(Session).model


class Invoice(models.Model):
    STATUS_DRAFT = 0
    STATUS_VALIDATED = 1
    STATUS_CHOICES = (
        (STATUS_DRAFT, _("Brouillon")),
        (STATUS_VALIDATED, _("Validée")),
    )

    generated_at = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(
        _("Statut"), choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    ref = models.CharField(_("Référence"), max_length=20, blank=False, unique=True)
    title = models.CharField(_("Titre"), max_length=255, blank=True)
    organization = models.ForeignKey(
        Organization,
        verbose_name=_("Établissement"),
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    season = models.ForeignKey(
        Season,
        verbose_name=_p("Singular month", "Mois"),
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    def __str__(self):
        return gettext(f"Facture {self.ref} pour {self.organization} / {self.season}")

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

    def sum_of(self, things: Iterable[str]):
        if self.pk:
            fields = sum(F(thing) for thing in things)
            return self.lines.aggregate(total=Sum(fields))["total"]
        return None

    def sum_cost_bikes_reduced(self):
        return sum([line.cost_bikes_reduced for line in self.lines.all()])

    def sum_cost(self):
        return self.sum_cost_bikes_reduced() + (self.sum_cost_participants or 0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate sum_* methods
        for thing in [
            "nb_bikes",
            "nb_participants",
            "cost_participants",
        ]:
            setattr(self, f"sum_{thing}", self.sum_of([thing]))

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

    @cached_property
    def settings(self):
        try:
            return AnnualStateSetting.objects.get(
                canton=self.organization.address_canton,
                year=self.season.year,
            )
        except AnnualStateSetting.DoesNotExist:
            return AnnualStateSetting()

    @property
    def is_up_to_date(self):
        """
        Check if the whole Invoice is up_to_date
        """
        # First check if the individual lines are OK.
        lines = self.lines.prefetch_related("session", "historical_session")
        if not all([line.is_up_to_date for line in lines.all()]):
            return False
        # Check if the invoice lines correspond to the concerned sessions
        if set(lines.values_list("session_id", flat=True)) != set(
            self.sessions.values_list("id", flat=True)
        ):
            return False
        return True

    @property
    def adjusted_sum_of_bikes(self):
        lines_per_day = dict()
        for line in self.lines.all():
            date_of_current_line = line.historical_session.day
            nb_bikes = lines_per_day.get(date_of_current_line, {}).get(
                "max_nb_bikes", 0
            )
            lines_per_day[date_of_current_line] = {
                "max_nb_bikes": max(line.nb_bikes, nb_bikes)
            }

        adjusted_sum_of_bikes = sum(
            [line["max_nb_bikes"] for _, line in lines_per_day.items()]
        )

        return adjusted_sum_of_bikes

    @property
    def month_of_the_invoice(self):
        return self.generated_at.strftime("%B")


def round_CHF(n: D):
    """
    Round a Decimal to 0.05 cents
    """
    return D((n * 20).quantize(D("1"), rounding=ROUND_HALF_EVEN) / 20).quantize(
        D("0.01")
    )


class InvoiceLine(models.Model):
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True)
    historical_session = models.ForeignKey(HistoricalSession, on_delete=models.PROTECT)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    nb_bikes = models.PositiveSmallIntegerField()
    nb_participants = models.PositiveSmallIntegerField()
    cost_bikes = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    cost_participants = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        unique_together = (("session", "invoice"),)
        ordering = ("historical_session__day", "historical_session__begin")

    def __str__(self):
        return gettext(
            f"{self.invoice.ref}: {self.historical_session} - Vélos: {self.nb_bikes} ({self.cost_bikes} CHF) - Participants: {self.nb_participants} ({self.cost_participants} CHF)"
        )

    @property
    def has_cost_bikes(self):
        """
        True when this line is the one accounting for the cost of bikes.
        There may be multiple lines (sessions) on the same day,
        but bikes are rented for the whole day.
        """
        last_line_with_most_bikes = (
            self.invoice.lines.filter(
                historical_session__day=self.historical_session.day
            )
            .order_by("-nb_bikes", "-historical_session__begin", "-id")
            .first()
        )
        return self == last_line_with_most_bikes

    @property
    def cost_bikes_reduced(self):
        if not self.has_cost_bikes:
            return 0
        # Sum of the costs, rounded to 5 cents.
        return round_CHF(
            D(self.cost_bikes * D(1 - self.cost_bikes_reduction_percent() / 100))
        )

    @property
    def cost(self):
        return self.cost_bikes_reduced + self.cost_participants

    def most_recent_historical_session(self):
        """
        Provide a shortcut to getting the latest historical copy of the session
        """
        try:
            return self.session.history.latest("history_date")
        except AttributeError:  # Without a self.session (deleted ?)
            return None

    def save(self, *args, **kwargs):
        """
        Safeguard against not having a historical_session
        """
        if not self.historical_session_id:
            self.historical_session = self.most_recent_historical_session()
        super().save(*args, **kwargs)

    @cached_property
    def is_up_to_date(self):
        """
        Check if that invoice line is up-to-date by comparing the historical session, number and costs
        """
        if not self.session:
            return False

        if (
            self.historical_session.history_id
            != self.most_recent_historical_session().history_id
        ):
            return False

        for t in ["bike", "participant"]:
            # Check if the nb_* is identical
            if getattr(self, f"nb_{t}s") != getattr(self.session, f"n_{t}s"):
                return False
            # Check if the calculated cost is identical
            if getattr(self, f"cost_{t}s") != getattr(
                self.session, f"n_{t}s"
            ) * getattr(self.invoice.settings, f"cost_per_{t}"):
                return False
        return True

    def cost_bikes_reduction_percent(self):
        """
        Compute the reduction in cost for bikes. Reductions are applied for consecutive days.
        """
        # Maps "consecutive days" to "percentage of reduction"
        reductions_in_percent = {2: 5, 3: 10, 4: 20, 5: 30}
        # Get the other lines of this invoice, with their daily differences to ours
        lines_diff_days = [
            diff_days.days
            for diff_days in self.invoice.lines.annotate(
                diff_days=(F("historical_session__day") - self.historical_session.day)
            ).values_list("diff_days", flat=True)
        ]

        max_days_diff_to_check = max(reductions_in_percent.keys())

        # Check the days before first
        nth_in_serie = 0
        while nth_in_serie < max_days_diff_to_check:
            if -nth_in_serie - 1 not in lines_diff_days:
                break
            nth_in_serie = nth_in_serie + 1
        # Check the days after
        followed_by = 0
        while followed_by < max_days_diff_to_check:
            if followed_by + 1 not in lines_diff_days:
                break
            followed_by = followed_by + 1
        # We now know we're in a sequence of that many lines:
        in_a_sequence_of = nth_in_serie + 1 + followed_by
        # Get me the reduction
        return reductions_in_percent.get(in_a_sequence_of, 0)

    def refresh(self):
        """
        Align the invoiceline's attributes
        """
        if self.session:
            self.historical_session = self.most_recent_historical_session()
            self.nb_bikes = self.session.n_bikes
            self.nb_participants = self.session.n_participants
            self.cost_bikes = self.invoice.settings.cost_per_bike * self.session.n_bikes
            self.cost_participants = (
                self.invoice.settings.cost_per_participant * self.session.n_participants
            )
        # Clear the cached is_up_to_date if possible
        try:
            del self.is_up_to_date
        except AttributeError:
            pass
