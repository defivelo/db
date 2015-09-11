# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from autocomplete_light import AutocompleteModelBase, register as al_register
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from apps.common.models import Address


@python_2_unicode_compatible
class Organization(Address, models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    name = models.CharField(_('Nom'), max_length=255)

    class Meta:
        verbose_name = _('Établissement')
        verbose_name_plural = _('Établissements')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organization-detail', args=[self.pk])


class OrganizationAutocomplete(AutocompleteModelBase):
    search_fields = ['name', 'address_city', 'address_street']
    model = Organization
al_register(OrganizationAutocomplete)
