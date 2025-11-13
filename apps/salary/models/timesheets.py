from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .. import BONUS_LEADER, HOURLY_RATE_HELPER, RATE_ACTOR


class Timesheet(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="timesheets",
        on_delete=models.CASCADE,
    )
    date = models.DateField(_("Date"), blank=True, null=True)

    time_helper = models.FloatField(_("Heures moni·teur·trice"), default=0)
    actor_count = models.IntegerField(_("Intervention(s)"), default=0)
    leader_count = models.IntegerField(
        _("Participation(s) comme Moniteur·trice 2"), default=0
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
    ignore = models.BooleanField(_("Ignorer"), default=False)

    class Meta:
        unique_together = (
            (
                "user",
                "date",
            ),
        )

    def get_total_amount_helper(self):
        if self.ignore:
            return 0
        return (
            (self.time_helper or 0) + self.overtime + self.traveltime
        ) * HOURLY_RATE_HELPER

    def get_total_amount_actor(self):
        if self.ignore:
            return 0
        return (self.actor_count or 0) * RATE_ACTOR

    def get_total_amount_leader(self):
        if self.ignore:
            return 0
        return (self.leader_count or 0) * BONUS_LEADER

    def get_total_amount(self):
        if self.ignore:
            return 0
        return (
            self.get_total_amount_actor()
            + self.get_total_amount_helper()
            + self.get_total_amount_leader()
        )
