from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Timesheet(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="timesheets", on_delete=models.CASCADE,
    )
    date = models.DateField(_("Date"), blank=True, null=True)

    time_helper = models.FloatField(_("Heure moniteur"), default=0)
    time_actor = models.FloatField(_("Heure intervenant"), default=0)

    overtime = models.FloatField(_("Heure(s) supplémentaire(s)"), default=0)
    traveltime = models.FloatField(_("Heure(s) de trajet"), default=0)
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
