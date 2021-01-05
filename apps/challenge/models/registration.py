from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.challenge.models import Session
from apps.orga.models import Organization

User = get_user_model()

REGISTRATION_MORNING = "08:30:00"
REGISTRATION_AFTERNOON = "13:30:00"

REGISTRATION_DAY_TIMES = (
    (REGISTRATION_MORNING, _("Matin")),
    (REGISTRATION_AFTERNOON, _("Après-midi")),
)


class Registration(models.Model):
    coordinator = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    date = models.DateField(_("Date"))
    day_time = models.CharField(
        verbose_name=_("Moment de la journée"),
        choices=REGISTRATION_DAY_TIMES,
        default=REGISTRATION_MORNING,
        max_length=8,
    )
    classes_amount = models.IntegerField(
        verbose_name=_("Nb de classes (1 à 6)"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
    )

    is_archived = models.BooleanField(verbose_name=_("Archivée"), default=False)

    def clean(self):
        if not self.coordinator.managed_organizations.filter(
            pk=self.organization.pk
        ).exists():
            raise ValidationError(
                {
                    "organization": _(
                        "L'établissement choisi n'est pas géré par cet utilisateur."
                    )
                }
            )

        if Session.session_exists(self.organization, self.date, self.day_time_as_time):
            raise ValidationError(
                {
                    "date": _(
                        "Il y a déjà une session inscrite pour cet établissement à cette date."
                    )
                }
            )

    def archive(self):
        self.is_archived = True
        self.save()

    @property
    def day_time_as_time(self):
        as_array = self.day_time.split(":")
        return time(int(as_array[0]), int(as_array[1]))
