# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField

from apps.challenge.models import QualificationActivity
from apps.common.models import Address
from localflavor.ch.ch_states import STATE_CHOICES
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField

FORMATION_M1 = 'M1'
FORMATION_M2 = 'M2'

FORMATION_CHOICES = (
    ('', '----------'),
    (FORMATION_M1, _('Moniteur 1')),
    (FORMATION_M2, _('Moniteur 2')),
)
FORMATION_KEYS = [k[0] for k in FORMATION_CHOICES if k[0] != '']

USERSTATUS_UNDEF = 0
USERSTATUS_ACTIVE = 10
USERSTATUS_RESERVE = 20
USERSTATUS_INACTIVE = 30
USERSTATUS_ARCHIVE = 30

USERSTATUS_CHOICES = (
    (USERSTATUS_UNDEF, '---------'),
    (USERSTATUS_ACTIVE, _('Actif')),
    (USERSTATUS_RESERVE, _('Réserve')),
    (USERSTATUS_INACTIVE, _('Inactif')),
    (USERSTATUS_ARCHIVE, _('Archive')),
)

BAGSTATUS_NONE = 0
BAGSTATUS_LOAN = 10
BAGSTATUS_PAID = 20

BAGSTATUS_CHOICES = (
    (BAGSTATUS_NONE, '---'),
    (BAGSTATUS_LOAN, _('En prêt')),
    (BAGSTATUS_PAID, _('Payé')),
)


@python_2_unicode_compatible
class UserProfile(Address, models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='profile',
                                primary_key=True)
    iban = IBANField(include_countries=IBAN_SEPA_COUNTRIES, blank=True)
    social_security = models.CharField(max_length=16, blank=True)
    natel = models.CharField(max_length=13, blank=True)
    activity_cantons = MultiSelectField(_("Cantons d'affiliation"),
                                        choices=STATE_CHOICES,
                                        blank=True)
    formation = models.CharField(_("Formation"), max_length=2,
                                 choices=FORMATION_CHOICES,
                                 blank=True)
    actor_for = models.ForeignKey(QualificationActivity,
                                  related_name='actors',
                                  limit_choices_to={'category': 'C'},
                                  null=True, blank=True)
    status = models.PositiveSmallIntegerField(
        _("Statut"),
        choices=USERSTATUS_CHOICES,
        default=USERSTATUS_UNDEF)
    status_updatetime = models.DateTimeField(null=True, blank=True)
    pedagogical_experience = models.TextField(_('Expérience pédagogique'),
                                              blank=True)
    firstmed_course = models.BooleanField(_('Cours samaritains'),
                                          default=False)
    firstmed_course_comm = models.CharField(
        _('Cours samaritains (spécifier)'),
        max_length=255,
        blank=True
    )
    bagstatus = models.PositiveSmallIntegerField(
        _("Statut"),
        choices=USERSTATUS_CHOICES,
        default=USERSTATUS_UNDEF)
    bagstatus_updatetime = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(_('Remarques'), blank=True)

    @property
    def formation_full(self):
        if self.formation:
            return dict(FORMATION_CHOICES)[self.formation]
        return ''

    @property
    def natel_int(self):
        if self.natel:
            # Delete spaces, drop initial 0, add +41
            return '+41' + self.natel.replace(' ', '')[1:]
        return ''

    def formation_icon(self):
        icon = ''
        title = self.formation_full
        if self.formation == FORMATION_M1:
            icon = 'tag'
        elif self.formation == FORMATION_M2:
            icon = 'tags'
        if icon:
            return mark_safe(
                '<span class="glyphicon glyphicon-{icon}" aria-hidden="true"'
                ' title="{title}"></span>'.format(
                    icon=icon,
                    title=title)
            )
        return ''

    @property
    def actor(self):
        return (self.actor_for is not None)

    def actor_icon(self):
        if self.actor:
            return mark_safe(
                '<span class="glyphicon glyphicon-sunglasses"'
                ' aria-hidden="true" title="{title}"></span>'.format(
                    title=self.actor_for.name)
            )
        return ''

    def __str__(self):
        return self.user.get_full_name()


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def User_pre_save(sender, **kwargs):
    if not kwargs['instance'].username:
        kwargs['instance'].username = uuid.uuid4().hex[0:30]
