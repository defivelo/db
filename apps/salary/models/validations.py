from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from parler.models import TranslatableModel, TranslatedFields

from apps.common import DV_STATE_CHOICES


class MonthlyCantonalValidationUrl(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_("Nom"), max_length=255),
        url=models.URLField(_("URL")),
        label=models.CharField(_("Label"), max_length=255, blank=True),
    )

    class Meta:
        verbose_name = _("URL pour validation mensuelle")
        verbose_name_plural = _("URLs pour validation mensuelle")

    def __str__(self):
        return self.name


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
    validated_urls = models.ManyToManyField(MonthlyCantonalValidationUrl)

    class Meta:
        unique_together = (
            (
                "canton",
                "date",
            ),
        )
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

    @property
    def validated(self):
        if self.validated_at is None:
            return False
        if self.validated_by is None:
            return False

        our_urls_pks = self.validated_urls.all().values_list("pk", flat=True)
        all_urls_pks = MonthlyCantonalValidationUrl.objects.all().values_list(
            "pk", flat=True
        )
        for url_pk in all_urls_pks:
            if url_pk not in our_urls_pks:
                return False
        return True
