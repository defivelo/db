from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

MORNING = "0"
AFTERNOON = "1"

DAY_TIMES = (
    (MORNING, _("Matin")),
    (AFTERNOON, _("Après-midi")),
)

User = get_user_model()

class Registration(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    date = models.DateField()
    day_time = models.CharField(choices=DAY_TIMES, default=MORNING, max_length=1)
    classes_amount = models.IntegerField(
        verbose_name=_("Nb de classes"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        help_text=_("15 à 25 participants par classe")
    )
