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

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField
from multiselectfield import MultiSelectField
from rolepermissions.verifications import has_role

from apps.challenge.models import QualificationActivity, Season
from apps.common import CANTONS_REGEXP, DV_STATE_CHOICES, DV_STATE_CHOICES_WITH_DEFAULT
from apps.common.models import Address
from defivelo.roles import user_cantons

from . import FORMATION_CHOICES, FORMATION_KEYS, FORMATION_M1, FORMATION_M2, get_new_username  # NOQA

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
    '      title="{title}"></span>'
)

PERSONAL_FIELDS = ['natel', 'birthdate',
                   'address_street', 'address_no', 'address_zip',
                   'address_city', 'address_canton',
                   'iban', 'social_security',
                   'status', 'activity_cantons',
                   ]

DV_PUBLIC_FIELDS = ['formation', 'formation_lastdate', 'actor_for',
                    'pedagogical_experience',
                    'firstmed_course', 'firstmed_course_comm',
                    'bagstatus', 'affiliation_canton',
                    ]

DV_PRIVATE_FIELDS = ['comments']

STD_PROFILE_FIELDS = PERSONAL_FIELDS + DV_PUBLIC_FIELDS + DV_PRIVATE_FIELDS


@python_2_unicode_compatible
class UserProfile(Address, models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='profile',
                                primary_key=True)
    birthdate = models.DateField(_('Date'), blank=True, null=True)
    iban = IBANField(include_countries=IBAN_SEPA_COUNTRIES, blank=True)
    social_security = models.CharField(max_length=16, blank=True)
    natel = models.CharField(max_length=13, blank=True)
    affiliation_canton = models.CharField(
        _("Canton d'affiliation"),
        choices=DV_STATE_CHOICES_WITH_DEFAULT,
        max_length=5,
        blank=True)
    activity_cantons = MultiSelectField(_("Défi Vélo mobile"),
                                        choices=DV_STATE_CHOICES,
                                        blank=True)
    formation = models.CharField(_("Formation"), max_length=2,
                                 choices=FORMATION_CHOICES,
                                 blank=True)
    formation_lastdate = models.DateField(_('Date de la dernière formation'),
                                          blank=True, null=True)
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

    def save(self, *args, **kwargs):
        if self.activity_cantons:
            # Remove the affiliation canton from the activity_cantons
            try:
                self.activity_cantons.remove(self.affiliation_canton)
            except (ValueError, AttributeError):
                pass
        super(UserProfile, self).save(*args, **kwargs)

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
            css_class = 'success'  # Green
        elif self.status == USERSTATUS_RESERVE:
            css_class = 'warning'  # Orange
        elif self.status == USERSTATUS_INACTIVE:
            css_class = 'danger'  # Red
        return css_class

    @property
    def age(self):
        today = timezone.now()
        return (
                today.year - self.birthdate.year -
                (
                    (today.month, today.day) <
                    (self.birthdate.month, self.birthdate.day)
                )
               )

    @property
    def iban_nice(self):
        if self.iban:
            value = self.iban
            # Code stolen from
            # https://django-localflavor.readthedocs.org/en/latest/_modules/localflavor/generic/forms/#IBANFormField.prepare_value
            grouping = 4
            value = value.upper().replace(' ', '').replace('-', '')
            return ' '.join(value[i:i + grouping] for i in
                            range(0, len(value), grouping))
        return ''

    def formation_icon(self):
        icon = ''
        title = self.formation_full
        if self.formation == FORMATION_M1:
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
            return [
                c[1] for c in DV_STATE_CHOICES
                if c[0] == self.affiliation_canton
                ][0]
        except IndexError:
            return ''

    @property
    def activity_cantons_verb(self):
        return [
            c[1] for c in DV_STATE_CHOICES
            if c[0] in self.activity_cantons
            ]

    def access_level(self, textonly=True):
        icon = ''
        title = ''
        if self.can_login:
            title = _('A accès')
            icon = 'user'

            if self.user.is_superuser:
                title = _('Administra·teur·trice')
                icon = 'queen'
            elif has_role(self.user, 'power_user'):
                title = _('Super-utilisa·teur·trice')
                icon = 'king'
            elif has_role(self.user, 'state_manager'):
                title = _('Chargé·e de projet')
                icon = 'bishop'
        if title and textonly:
            return title
        if icon:
            return mark_safe(STDGLYPHICON.format(icon=icon, title=title))
        return ''

    def access_level_icon(self):
        return self.access_level(False)

    @property
    def access_level_text(self):
        return self.access_level(True)

    @property
    def managed_cantons(self):
        return [m.canton for m in self.user.managedstates.all()]

    @property
    def managed_cantons_verb(self):
        return [
            c[1] for c in DV_STATE_CHOICES
            if c[0] in self.managed_cantons
            ]

    @property
    def mailtolink(self):
        return (
            '{name} <{email}>'.format(
                name=self.user.get_full_name(),
                email=self.user.email)
            )

    @property
    def can_login(self):
        return self.user.is_active and self.user.has_usable_password

    def send_credentials(self, context, force=False):
        if self.can_login and not force:
            # Has credentials already
            raise ValidationError(_('A déjà des données de connexion'),
                                  code='has_login')

        newpassword = get_user_model().objects.make_random_password()
        self.user.set_password(newpassword)
        self.user.is_active = True

        context['userprofile'] = self.user
        context['password'] = newpassword
        self.user.save()

        # This can raise exception, but that's good
        send_mail(
            _('Accès au site \'{site_name}\'').format(
                site_name=context['current_site'].name),
            render_to_string(
                'auth/email_user_send_credentials.txt',
                context),
            settings.DEFAULT_FROM_EMAIL,
            [self.mailtolink, ]
            )

        # Create a validated email
        EmailAddress.objects.get_or_create(
            user=self.user, email=self.user.email, verified=True,
            primary=True
            )

    def get_seasons(self, raise_without_cantons=False):
        qs = Season.objects
        usercantons = []

        try:
            # Obtient les cantons gérés
            usercantons = user_cantons(self.user)
        except LookupError:
            if raise_without_cantons:
                raise PermissionDenied

        # Ajoute les cantons d'affiliation et mobiles
        if self.formation or self.actor_for:
            if self.affiliation_canton:
                usercantons += [self.affiliation_canton]
            if self.activity_cantons:
                usercantons += self.activity_cantons

        # Unique'ify, discard empty values
        usercantons = set([c for c in usercantons if c])

        if usercantons:
            cantons_regexp = CANTONS_REGEXP % "|".join(usercantons)
            return qs.filter(cantons__regex=cantons_regexp)

        return qs.none()

    def __str__(self):
        return self.user.get_full_name()

    class Meta:
        verbose_name = _('Profil')
        verbose_name_plural = _('Profils')


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def User_pre_save(sender, **kwargs):
    if not kwargs['instance'].username:
        kwargs['instance'].username = get_new_username()
        # Mark new users as inactive, to not let them get a login
        kwargs['instance'].is_active = False


@python_2_unicode_compatible
class UserManagedState(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='managedstates',
                             limit_choices_to={'is_active': True},)
    canton = models.CharField(_('Canton'), max_length=5,
                              choices=DV_STATE_CHOICES)

    @property
    def canton_full(self):
        return [c[1] for c in DV_STATE_CHOICES
                if c[0] == self.address_canton][0]

    def __str__(self):
        return _('{name} est chargé·e de projet pour le canton '
                 '{canton}').format(
                     name=self.user.get_full_name(),
                     canton=self.canton)

    class Meta:
        verbose_name = _('Canton géré')
        verbose_name_plural = _('Cantons gérés')
        unique_together = (('user', 'canton'), )
