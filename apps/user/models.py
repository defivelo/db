# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015 Didier Raboud <me+defivelo@odyx.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField
from multiselectfield import MultiSelectField

from apps.challenge.models import QualificationActivity
from apps.common import DV_STATE_CHOICES, DV_STATE_CHOICES_WITH_DEFAULT
from apps.common.models import Address

from . import FORMATION_CHOICES, FORMATION_KEYS, FORMATION_M1, FORMATION_M2

USERSTATUS_UNDEF = 0
USERSTATUS_ACTIVE = 10
USERSTATUS_RESERVE = 20
USERSTATUS_INACTIVE = 30
USERSTATUS_ARCHIVE = 40

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

STDGLYPHICON = (
    '<span class="glyphicon glyphicon-{icon}" aria-hidden="true"'
    '      title="{title}"></span> '
)

STD_PROFILE_FIELDS = ['natel', 'birthdate',
                      'address_street', 'address_no', 'address_zip',
                      'address_city', 'address_canton',
                      'iban', 'social_security',
                      'office_member',
                      'formation', 'actor_for', 'status',
                      'pedagogical_experience',
                      'firstmed_course', 'firstmed_course_comm',
                      'bagstatus', 'affiliation_canton', 'comments']

@python_2_unicode_compatible
class UserProfile(Address, models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='profile',
                                primary_key=True)
    birthdate = models.DateField(_('Date'), blank=True, null=True)
    iban = IBANField(include_countries=IBAN_SEPA_COUNTRIES, blank=True)
    social_security = models.CharField(max_length=16, blank=True)
    natel = models.CharField(max_length=13, blank=True)
    affiliation_canton = models.CharField(_("Canton d'affiliation"),
                                        choices=DV_STATE_CHOICES_WITH_DEFAULT,
                                        max_length=2,
                                        blank=False)
    office_member = models.BooleanField(_('Bureau Défi Vélo'),
                                          default=False)
    formation = models.CharField(_("Formation"), max_length=2,
                                 choices=FORMATION_CHOICES,
                                 blank=True)
    actor_for = models.ForeignKey(QualificationActivity,
                                  verbose_name=_('Intervenant'),
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
        _('Sac Défi Vélo'),
        choices=BAGSTATUS_CHOICES,
        default=BAGSTATUS_NONE)
    bagstatus_updatetime = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(_('Remarques'), blank=True)

    @property
    def formation_full(self):
        if self.formation:
            return dict(FORMATION_CHOICES)[self.formation]
        return ''

    @property
    def status_full(self):
        if self.status:
            return dict(USERSTATUS_CHOICES)[self.status]
        return ''

    def status_icon(self):
        icon = ''
        title = self.status_full
        if self.status == USERSTATUS_ACTIVE:
            icon = 'star'
        elif self.status == USERSTATUS_RESERVE:
            icon = 'star-empty'
        elif self.status == USERSTATUS_INACTIVE:
            icon = 'hourglass'
        elif self.status == USERSTATUS_ARCHIVE:
            icon = 'folder-close'
        if icon:
            return mark_safe(STDGLYPHICON.format(icon=icon, title=title))
        return ''

    def status_class(self):
        css_class = 'default'
        if self.status == USERSTATUS_ACTIVE:
            css_class = 'success' # Green
        elif self.status == USERSTATUS_RESERVE:
            css_class = 'warning' # Orange
        elif self.status == USERSTATUS_INACTIVE:
            css_class= 'danger'  # Red
        return css_class

    @property
    def age(self):
        today = timezone.now()
        return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
    
    @property
    def natel_int(self):
        if self.natel:
            # Delete spaces, drop initial 0, add +41
            return '+41' + self.natel.replace(' ', '')[1:]
        return ''

    @property
    def iban_nice(self):
        if self.iban:
            value = self.iban
            # Code stolen from https://django-localflavor.readthedocs.org/en/latest/_modules/localflavor/generic/forms/#IBANFormField.prepare_value
            grouping = 4
            value = value.upper().replace(' ', '').replace('-', '')
            return ' '.join(value[i:i + grouping] for i in range(0, len(value), grouping))
        return ''

    def formation_icon(self):
        icon = ''
        title = self.formation_full
        if self.office_member:
            icon = 'tower'
            title = _('Bureau Défi Vélo')
        elif self.formation == FORMATION_M1:
            icon = 'tag'
        elif self.formation == FORMATION_M2:
            icon = 'tags'
        if icon:
            return mark_safe(STDGLYPHICON.format(icon=icon, title=title))
        return ''

    @property
    def actor(self):
        return (self.actor_for is not None)

    def actor_icon(self):
        if self.actor:
            return mark_safe(STDGLYPHICON.format(icon='sunglasses',
                                                 title=self.actor_for))
        return ''

    @property
    def bagstatus_full(self):
        if self.bagstatus:
            return dict(BAGSTATUS_CHOICES)[self.bagstatus]
        return ''

    def bagstatus_icon(self):
        icon = ''
        title = self.bagstatus_full
        if self.bagstatus == BAGSTATUS_NONE:
            icon = 'unchecked'
        elif self.bagstatus == BAGSTATUS_LOAN:
            icon = 'new-window'
        elif self.bagstatus == BAGSTATUS_PAID:
            icon = 'check'
        if icon:
            return mark_safe(STDGLYPHICON.format(icon=icon, title=title))
        return ''

    @property
    def affiliation_canton_verb(self):
        try:
            return [c[1] for c in DV_STATE_CHOICES if c[0] == self.affiliation_canton][0]
        except IndexError:
            return ''

    def __str__(self):
        return self.user.get_full_name()


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def User_pre_save(sender, **kwargs):
    if not kwargs['instance'].username:
        kwargs['instance'].username = uuid.uuid4().hex[0:30]
        # Mark new users as inactive, to not let them get a login
        kwargs['instance'].is_active = False
