from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.common import DV_STATE_CHOICES

from . import BONUS_LEADER, HOURLY_RATE_HELPER, RATE_ACTOR


class Timesheet(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="timesheets", on_delete=models.CASCADE,
    )
    date = models.DateField(_("Date"), blank=True, null=True)

    time_helper = models.FloatField(_("Heures moni·teur·trice"), default=0)
    actor_count = models.IntegerField(_("Intervention(s)"), default=0)
    leader_count = models.IntegerField(
        _("Participation(s) comme moniteur 2"), default=0
    )

    overtime = models.FloatField(_("Heures supplémentaires"), default=0)
    traveltime = models.FloatField(_("Heures de trajet"), default=0)
    comments = models.TextField(_("Remarques"), blank=True)

    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        unique_together = (("user", "date",),)

    def get_total_amount_helper(self):
        return (
            (self.time_helper or 0) + self.overtime + self.traveltime
        ) * HOURLY_RATE_HELPER

    def get_total_amount_actor(self):
        return (self.actor_count or 0) * RATE_ACTOR

    def get_total_amount_leader(self):
        return (self.leader_count or 0) * BONUS_LEADER

    def get_total_amount(self):
        return (
            self.get_total_amount_actor()
            + self.get_total_amount_helper()
            + self.get_total_amount_leader()
        )


class MonthlyCantonalValidation(models.Model):
    date = models.DateField("Date (1er du mois)")
    canton = models.CharField(
        _("Canton"),
        max_length=2,
        choices=DV_STATE_CHOICES,
        unique_for_month="date",
        unique_for_year="date",
    )
    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        unique_together = (("canton", "date",),)
        verbose_name = _("Validation mensuelle cantonale")
        verbose_name_plural = _("Validations mensuelles cantonales")
        ordering = ["date", "canton"]

    def __str__(self):
        return _("{year}/{month}: Validation du canton {canton}").format(
            year=self.date.year, month=self.date.month, canton=self.canton
        )

    def save(self, *args, **kwargs):
        """
        Enforce date to get day=1
        """
        self.date = self.date.replace(day=1)
        super().save(*args, **kwargs)
