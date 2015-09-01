import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', primary_key=True)
    iban = IBANField(include_countries=IBAN_SEPA_COUNTRIES, blank=True)
    address_street = models.CharField(max_length=255, blank=True)
    address_no = models.CharField(max_length=8, blank=True)
    address_zip = models.CharField(max_length=4, blank=True)
    address_city = models.CharField(max_length=64, blank=True)
    address_canton = models.CharField(max_length=2, blank=True)
    natel = models.CharField(max_length=12, blank=True)


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def User_pre_save(sender, **kwargs):
    if not kwargs['instance'].username:
        kwargs['instance'].username = uuid.uuid4().hex
