# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import date
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from apps.common.models import Address
from apps.orga.models import Organization

DEFAULT_SESSION_DURATION_HOURS = 3
DEFAULT_EARLY_MINUTES_FOR_HELPERS_MEETINGS = 60


@python_2_unicode_compatible
class Session(Address, models.Model):
    created_on = models.DateTimeField(auto_now_add=True)

    # Time span
    day = models.DateField(_('Date'), blank=True)
    begin = models.TimeField(_('Début'), blank=True, null=True)
    duration = models.DurationField(_('Durée'),
                                    default=timedelta(
                                        hours=DEFAULT_SESSION_DURATION_HOURS
                                        ))
    organization = models.ForeignKey(Organization,
                                     verbose_name=_('Établissement'),
                                     related_name='sessions',
                                     blank=True, null=True)
    FALLBACK_CHOICES = (
        ('A', _('Programme déluge')),
        ('B', _('Annulation')),
        ('C', _('Report …')),
        ('D', _('Autre …')),
    )
    fallback_plan = models.CharField(_("Mauvais temps"), max_length=1,
                                     choices=FALLBACK_CHOICES, blank=True)
    helpers_time = models.TimeField(_('Heure rendez-vous moniteurs'),
                                    null=True, blank=True)
    helpers_place = models.CharField(_("Lieu rendez-vous moniteurs"),
                                     max_length=512, blank=True)
    apples = models.CharField(_("Pommes"), max_length=512, blank=True)
    comments = models.TextField(_('Remarques'), blank=True)

    class Meta:
        verbose_name = _('Session')
        verbose_name_plural = _('Sessions')
        unique_together = (('organization', 'begin', 'day'),)
        ordering = ['day', 'begin', 'organization__name']

    @property
    def errors(self):
        errors = []
        if not self.begin or not self.duration:
            errors.append(_('Horaire'))
        if not self.fallback_plan:
            errors.append(_('Mauvais temps'))
        if not self.apples:
            errors.append(_('Pommes'))
        # Check the qualifications
        qualiq = 0
        for quali in self.qualifications.all():
            qualiq += 1
            if quali.errors:
                errors.append(_('Quali : {name}').format(name=quali.name))
        if qualiq == 0:
            errors.append(_('Pas de qualifications'))
        if errors:
            return mark_safe(
                '<br />'.join(
                    [
                        '<span class="btn-warning btn-xs disabled">'
                        '  <span class="glyphicon glyphicon-warning-sign"></span>'
                        '  {error}'
                        '</span>'.format(error=e) for e in errors
                    ])
                )

    @property
    def fallback(self):
        if self.fallback_plan:
            return dict(self.FALLBACK_CHOICES)[self.fallback_plan]
        return ''

    @property
    def end(self):
        if self.begin and self.duration:
            day = self.day if self.day else datetime.today()
            end = datetime.combine(day, self.begin) + self.duration
            return end.time()

    def helpers_time_with_default(self):
        if self.helpers_time:
            return self.helpers_time
        if self.begin:
            # Compute a default value with regards to the start time
            helpers_time = (
                datetime.combine(datetime.today(), self.begin) -
                timedelta(minutes=DEFAULT_EARLY_MINUTES_FOR_HELPERS_MEETINGS)
                ).time().strftime('%H:%M')
            return mark_safe('<em>{}</em>'.format(helpers_time))
        return ''

    def __str__(self):
        return '{date}{begin}{orga}'.format(
            date=date(self.day, settings.DATE_FORMAT),
            begin=' (%s)' % self.begin if self.begin else '',
            orga=' - %s' % self.organization.name if self.organization else ''
            )
