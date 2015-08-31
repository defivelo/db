# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import date
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from apps.orga.models import Organization


@python_2_unicode_compatible
class SessionTimeSlot(models.Model):
    begin = models.TimeField(_('Début'))
    end = models.TimeField(_('Fin'))

    class Meta:
        verbose_name = _('Horaire pour sessions')
        verbose_name_plural = _('Horaires pour sessions')
        ordering = ['begin', 'end']

    def __str__(self):
        return '%s - %s' % (
            self.begin.strftime('%H:%M'),
            self.end.strftime('%H:%M')
            )


@python_2_unicode_compatible
class Session(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)

    # Time span
    day = models.DateField(_('Date'), blank=True)
    timeslot = models.ForeignKey(SessionTimeSlot,
                                 related_name='sessions',
                                 blank=True, null=True)
    organization = models.ForeignKey(Organization, related_name='sessions',
                                     blank=True, null=True)

    class Meta:
        verbose_name = _('Session')
        verbose_name_plural = _('Sessions')
        unique_together = (('organization', 'timeslot', 'day'),)
        ordering = ['day', 'timeslot__begin', 'organization__name']

    def get_absolute_url(self):
        return reverse('session-detail', args=[self.pk])

    def __str__(self):
        return '{date}{timeslot}{orga}'.format(
            date=date(self.day, settings.DATE_FORMAT),
            timeslot=' (%s)' % self.timeslot if self.timeslot else '',
            orga=' - %s' % self.organization.name if self.organization else ''
            )
