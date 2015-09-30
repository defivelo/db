# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import date
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField

from localflavor.ch.ch_states import STATE_CHOICES

from .session import Session


@python_2_unicode_compatible
class Season(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    begin = models.DateField(_('Début'))
    end = models.DateField(_('Fin'))
    cantons = MultiSelectField(_('Cantons'), choices=STATE_CHOICES)
    leader = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('Chargé de projet'),
                               blank=True, null=True)

    class Meta:
        verbose_name = _('Saison')
        verbose_name_plural = _('Saisons')
        ordering = ['begin', 'end', ]

    @property
    def cantons_verb(self):
        if self.cantons:
            return [c[1] for c in STATE_CHOICES if c[0] in self.cantons]

    @property
    def sessions(self):
        return Session.objects.filter(
            organization__address_canton__in=self.cantons,
            day__gte=self.begin,
            day__lt=self.end
            )

    @property
    def sessions_with_qualifs(self):
        return self.sessions.annotate(models.Count('qualifications')).filter(
            qualifications__count__gt=0,
            )

    def get_absolute_url(self):
        return reverse('season-detail', args=[self.pk])

    def desc(self):
        return _('{depuis_mois} à {jusqu_mois} ({cantons})').format(
            depuis_mois=date(self.begin, "F").title(),
            jusqu_mois=date(self.end, "F Y"),
            cantons=", ".join(self.cantons),
            )

    def __str__(self):
        return (
            self.desc() +
            (" - " + self.leader.get_full_name() if self.leader else '')
        )
