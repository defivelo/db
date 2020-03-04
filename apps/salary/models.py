from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from apps.salary.fields import DurationField


class Timesheet(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="timesheets", on_delete=models.CASCADE,
    )
    date = models.DateField(_("Date"), blank=True, null=True)

    time_monitor = DurationField(_("Heure moniteur"), blank=True, null=True)
    time_actor = DurationField(_("Heure intervenant"), blank=True, null=True)

    overtime = models.FloatField(_("Heure(s) supplémentaire(s)"), default=0)
    traveltime = models.FloatField(_("Heure(s) de trajet"), default=0)

    validated_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(_("Remarques"), blank=True)

    class Meta:
        unique_together = (("user", "date",),)
