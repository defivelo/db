# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Address(models.Model):
    address_street = models.CharField(_('Rue'), max_length=255, blank=True)
    address_no = models.CharField(_('N°'), max_length=8, blank=True)
    address_zip = models.CharField(_('NPA'), max_length=4, blank=True)
    address_city = models.CharField(_('Ville'), max_length=64, blank=True)
    address_canton = models.CharField(_('Canton'), max_length=2, blank=True)
