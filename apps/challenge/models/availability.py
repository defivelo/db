# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from .session import Session


@python_2_unicode_compatible
class HelperSessionAvailability(models.Model):
    AVAILABILITY_CHOICES = (
        ('y', _('Oui')),
        ('i', _('Si nécessaire')),
        ('n', _('Non')),
    )
    created_on = models.DateTimeField(auto_now_add=True)
    session = models.ForeignKey(Session, verbose_name=_('Session'),
                                related_name='availability_statuses')
    helper = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('Moniteur'),
                               related_name='availabilities',
                               limit_choices_to={'profile__isnull': False})
    availability = models.CharField(_("Disponible"), max_length=1,
                                    choices=AVAILABILITY_CHOICES)

    class Meta:
        verbose_name = _('Disponibilité par session')
        verbose_name_plural = _('Disponibilités par session')
        ordering = ['session', 'helper', 'availability']
        unique_together = (('session', 'helper', ), )

    def __str__(self):
        is_available = _("n'est pas disponible")
        if self.availability == 'y':
            is_available = _('est disponible')
        elif self.availability == 'i':
            is_available = _('est disponible si nécessaire')

        return _('{session}: {helper} {is_available}').format(
             session=self.session,
             helper=self.helper.get_full_name(),
             is_available=is_available)
