from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Timesheet(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="timesheets", on_delete=models.CASCADE,
    )
    date = models.DateField(_("Date"), blank=True, null=True)

    time_helper = models.FloatField(_("Heures moni·teur·trice"), default=0)
    time_actor = models.FloatField(_("Heures intervenant·e"), default=0)

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
