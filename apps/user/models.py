from django.conf import settings
from django.db import models
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', primary_key=True)
    iban = IBANField(include_countries=IBAN_SEPA_COUNTRIES)
