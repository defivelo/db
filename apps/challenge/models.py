# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import date
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

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
                                 verbose_name=_('Horaire'),
                                 related_name='sessions',
                                 blank=True, null=True)
    organization = models.ForeignKey(Organization,
                                     verbose_name=_('Établissement'),
                                     related_name='sessions',
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


@python_2_unicode_compatible
class SessionActivity(TranslatableModel):
    CATEGORY_CHOICES = (
        ('A', _('Vélo dans la rue')),
        ('B', _('Mécanique')),
        ('C', _('Rencontre')),
    )
    translations = TranslatedFields(
        name = models.CharField(_('Nom'), max_length=255)
    )
    category = models.CharField(_("Catégorie"), max_length=1,
                                choices=CATEGORY_CHOICES, blank=True)

    class Meta:
        verbose_name = _('Poste')
        verbose_name_plural = _('Postes')
        ordering = ['category', 'pk']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Qualification(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    name = models.CharField(_('Nom'), max_length=255)  # TODO: Replace with automated or classes objects
    session = models.ForeignKey(Session,
                                related_name='qualifications')
    activity_A = models.ForeignKey(SessionActivity,
                                   limit_choices_to={'category': 'A'},
                                   verbose_name=_('Vélo dans la rue'),
                                   related_name='sessions_A',
                                   blank=True, null=True
                                   )
    activity_B = models.ForeignKey(SessionActivity,
                                   limit_choices_to={'category': 'B'},
                                   verbose_name=_('Mécanique'),
                                   related_name='sessions_B',
                                   blank=True, null=True
                                   )
    activity_C = models.ForeignKey(SessionActivity,
                                   limit_choices_to={'category': 'C'},
                                   verbose_name=_('Rencontre'),
                                   related_name='sessions_C',
                                   blank=True, null=True
                                   )

    class Meta:
        verbose_name = _('Qualification')
        verbose_name_plural = _('Qualifications')
        ordering = ['session', 'created_on', 'name']

    def __str__(self):
        return '{name} ({session})'.format(
            name=self.name,
            session=self.session
            )
