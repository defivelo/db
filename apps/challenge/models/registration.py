from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

REGISTRATION_MORNING = 0
REGISTRATION_AFTERNOON = 1

REGISTRATION_DAY_TIMES = (
    (REGISTRATION_MORNING, _("Matin")),
    (REGISTRATION_AFTERNOON, _("Après-midi")),
)

User = get_user_model()


class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(_("Date"))
    day_time = models.IntegerField(
        choices=REGISTRATION_DAY_TIMES, default=REGISTRATION_MORNING
    )
    classes_amount = models.IntegerField(
        verbose_name=_("Nb de classes (1 à 6)"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
    )
