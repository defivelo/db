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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import smart_text
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as u
from django.utils.translation import ugettext_lazy as _

from allauth.account.models import EmailAddress
from django_countries.fields import CountryField
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField
from memoize import delete_memoized, memoize
from multiselectfield import MultiSelectField
from rolepermissions.checkers import has_role
from rolepermissions.roles import assign_role, clear_roles

from apps.challenge.models import QualificationActivity, Season
from apps.common import (
    DV_LANGUAGES,
    DV_LANGUAGES_WITH_DEFAULT,
    DV_SEASON_STATE_PLANNING,
    DV_STATE_CHOICES,
    DV_STATE_CHOICES_WITH_DEFAULT,
    MULTISELECTFIELD_REGEXP,
    STDGLYPHICON,
)
from apps.common.models import Address
from defivelo.roles import has_permission, user_cantons

from . import FORMATION_CHOICES, formation_short, get_new_username

USERSTATUS_UNDEF = 0
USERSTATUS_ACTIVE = 10
USERSTATUS_RESERVE = 20
USERSTATUS_INACTIVE = 30
USERSTATUS_ARCHIVE = 40
USERSTATUS_DELETED = 99

USERSTATUS_CHOICES = (
    (USERSTATUS_UNDEF, "---------"),
    (USERSTATUS_ACTIVE, _("Actif")),
    (USERSTATUS_RESERVE, _("Réserve")),
    (USERSTATUS_INACTIVE, _("Inactif")),
    (USERSTATUS_ARCHIVE, _("Archive")),
    (USERSTATUS_DELETED, _("Supprimé")),
)

USERSTATUS_CHOICES_NORMAL = tuple([us for us in USERSTATUS_CHOICES if us[0] < 90])

MARITALSTATUS_UNDEF = 0
MARITALSTATUS_SINGLE = 10
MARITALSTATUS_MARRIED = 20
MARITALSTATUS_DIVORCED = 30
MARITALSTATUS_WIDOW = 40
MARITALSTATUS_PACS = 50

MARITALSTATUS_CHOICES = (
    (MARITALSTATUS_UNDEF, "---------"),
    (MARITALSTATUS_SINGLE, _("Célibataire")),
    (MARITALSTATUS_MARRIED, _("Marié·e")),
    (MARITALSTATUS_DIVORCED, _("Divorcé·e")),
    (MARITALSTATUS_WIDOW, _("Veu·f·ve")),
    (MARITALSTATUS_PACS, _("En partenariat enregistré")),
)

BAGSTATUS_NONE = 0
BAGSTATUS_LOAN = 10
BAGSTATUS_PAID = 20
BAGSTATUS_GIFT = 30

BAGSTATUS_CHOICES = (
    (BAGSTATUS_NONE, "---"),
    (BAGSTATUS_LOAN, _("En prêt")),
    (BAGSTATUS_PAID, _("Payé")),
    (BAGSTATUS_GIFT, _("Offert")),
)

PERSONAL_FIELDS = [
    "language",
    "languages_challenges",
    "natel",
    "phone",
    "birthdate",
    "address_street",
    "address_no",
    "address_zip",
    "address_city",
    "address_canton",
    "nationality",
    "work_permit",
    "tax_jurisdiction",
    "bank_name",
    "iban",
    "cresus_employee_number",
    "social_security",
    "marital_status",
    "status",
    "activity_cantons",
]

DV_PUBLIC_FIELDS = [
    "formation",
    "formation_firstdate",
    "formation_lastdate",
    "actor_for",
    "pedagogical_experience",
    "firstmed_course",
    "firstmed_course_comm",
    "bagstatus",
    "affiliation_canton",
]

DV_PRIVATE_FIELDS = ["comments"]

STD_PROFILE_FIELDS = PERSONAL_FIELDS + DV_PUBLIC_FIELDS + DV_PRIVATE_FIELDS


class ExistingUserProfileManager(models.Manager):
    def get_queryset(self):
        return (
            super(ExistingUserProfileManager, self)
            .get_queryset()
            .exclude(status=USERSTATUS_DELETED)
        )


class UserProfile(Address, models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="profile",
        primary_key=True,
        on_delete=models.CASCADE,
    )
    cresus_employee_number = models.CharField(
        _("Numéro d'employé Crésus"), max_length=63, blank=True
    )
    language = models.CharField(
        _("Langue"), max_length=7, choices=DV_LANGUAGES_WITH_DEFAULT, blank=True
    )
    languages_challenges = MultiSelectField(
        _("Prêt à animer en"), choices=DV_LANGUAGES, blank=True
    )
    birthdate = models.DateField(_("Date de naissance"), blank=True, null=True)
    nationality = CountryField(_("Nationalité"), default="CH")
    work_permit = models.CharField(_("Permis de travail"), max_length=255, blank=True)
    tax_jurisdiction = models.CharField(
        _("Lieu d'imposition"), max_length=511, blank=True
    )
    bank_name = models.CharField(_("Nom de la banque"), max_length=511, blank=True)
    iban = IBANField(
        _("Coordonnées bancaires (IBAN)"),
        include_countries=IBAN_SEPA_COUNTRIES,
        blank=True,
    )
    social_security = models.CharField(_("N° AVS"), max_length=16, blank=True)
    natel = models.CharField(max_length=13, blank=True)
    phone = models.CharField(_("Téléphone"), max_length=13, blank=True)
    affiliation_canton = models.CharField(
        _("Canton d'affiliation"),
        choices=DV_STATE_CHOICES_WITH_DEFAULT,
        max_length=5,
        blank=True,
    )
    activity_cantons = MultiSelectField(
        _("Défi Vélo mobile"), choices=DV_STATE_CHOICES, blank=True
    )
    formation = models.CharField(
        _("Formation"), max_length=2, choices=FORMATION_CHOICES, blank=True
    )
    formation_firstdate = models.DateField(
        _("Date de la première formation"), blank=True, null=True
    )
    formation_lastdate = models.DateField(
        _("Date de la dernière formation"), blank=True, null=True
    )
    actor_for = models.ManyToManyField(
        QualificationActivity,
        verbose_name=_("Intervenant"),
        related_name="actor_for",
        limit_choices_to={"category": "C"},
        blank=True,
    )
    marital_status = models.PositiveSmallIntegerField(
        _("État civil"), choices=MARITALSTATUS_CHOICES, default=MARITALSTATUS_UNDEF
    )
    status = models.PositiveSmallIntegerField(
        _("Statut"), choices=USERSTATUS_CHOICES, default=USERSTATUS_ACTIVE
    )
    status_updatetime = models.DateTimeField(null=True, blank=True)
    pedagogical_experience = models.TextField(_("Expérience pédagogique"), blank=True)
    firstmed_course = models.BooleanField(_("Cours samaritains"), default=False)
    firstmed_course_comm = models.CharField(
        _("Cours samaritains (spécifier)"), max_length=255, blank=True
    )
    bagstatus = models.PositiveSmallIntegerField(
        _("Sac Défi Vélo"), choices=BAGSTATUS_CHOICES, default=BAGSTATUS_NONE
    )
    bagstatus_updatetime = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(_("Remarques"), blank=True)

    objects = models.Manager()
    objects_existing = ExistingUserProfileManager()

    def save(self, *args, **kwargs):
        if self.activity_cantons:
            # Remove the affiliation canton from the activity_cantons
            try:
                self.activity_cantons.remove(self.affiliation_canton)
            except (ValueError, AttributeError):
                pass
        if self.languages_challenges:
            if not self.language:
                self.language = self.languages_challenges.pop(0)
            # Remove the main language from the languages_challenges
            try:
                self.languages_challenges.remove(self.language)
            except (ValueError, AttributeError):
                pass
        # Assign the "collaborator" role automatically for "with formation" and "actors"
        if not (
            has_role(self.user, "power_user")
            or has_role(self.user, "state_manager")
            or has_role(self.user, "coordinator")
        ):
            # Make sure to use the uncached properties
            try:
                del self.actor
            except AttributeError:
                pass

            if self.formation or self.actor:
                self.set_role("collaborator")
            else:
                # Remove the role
                self.set_role()

        self.reset_cache()
        super().save(*args, **kwargs)

    def reset_cache(self):
        delete_memoized(has_permission)
        delete_memoized(user_cantons, self.user)
        delete_memoized(self.get_seasons)

    def set_role(self, role_str=None):
        # Enforce that a user can only have one role at a time
        clear_roles(self.user)
        if role_str:
            assign_role(self.user, role_str)
        self.reset_cache()

    def set_statemanager_for(self, states=[]):
        for ums in self.user.managedstates.all():
            if ums.canton not in states:
                ums.delete()
            else:
                states.remove(ums.canton)
        for canton in states:
            UserManagedState.objects.get_or_create(user=self.user, canton=canton)
        self.reset_cache()

    def send_credentials(self, context, force=False):
        if self.can_login and not force:
            # Has credentials already
            raise ValidationError(
                _("A déjà des données de connexion"), code="has_login"
            )

        newpassword = get_user_model().objects.make_random_password()
        self.user.set_password(newpassword)
        self.user.is_active = True

        context["userprofile"] = self.user
        context["password"] = newpassword
        self.user.save()

        # This can raise exception, but that's good
        self.send_mail(
            (settings.EMAIL_SUBJECT_PREFIX + u("Accès à l'Intranet")),
            render_to_string("auth/email_user_send_credentials.txt", context),
        )

        # Create a validated email
        EmailAddress.objects.get_or_create(
            user=self.user, email=self.user.email, verified=True, primary=True
        )

    @transaction.atomic
    def delete(self):
        self.user.is_active = False
        email_comment = _("Email avant suppression: %s") % self.user.email
        self.user.email = ""
        self.user.set_unusable_password()
        self.user.save()
        self.comments = (
            f"{self.comments}\n{email_comment}" if self.comments else email_comment
        )
        self.status = USERSTATUS_DELETED
        self.save()

    @cached_property
    def formation_full(self):
        if self.formation:
            return dict(FORMATION_CHOICES)[self.formation]
        return ""

    @cached_property
    def status_full(self):
        if self.status:
            return dict(USERSTATUS_CHOICES)[self.status]
        return ""

    @cached_property
    def marital_status_full(self):
        if self.marital_status:
            return dict(MARITALSTATUS_CHOICES)[self.marital_status]
        return ""

    def status_icon(self):
        icon = ""
        title = self.status_full
        if self.status == USERSTATUS_ACTIVE:
            icon = "star"
        elif self.status == USERSTATUS_RESERVE:
            icon = "star-empty"
        elif self.status == USERSTATUS_INACTIVE:
            icon = "hourglass"
        elif self.status == USERSTATUS_ARCHIVE:
            icon = "folder-close"
        elif self.status == USERSTATUS_DELETED:
            icon = "trash"
        if icon:
            return mark_safe(STDGLYPHICON.format(icon=icon, title=title))
        return ""

    def status_class(self):
        css_class = "default"
        if self.status == USERSTATUS_ACTIVE:
            css_class = "success"  # Green
        elif self.status == USERSTATUS_RESERVE:
            css_class = "warning"  # Orange
        elif self.status == USERSTATUS_INACTIVE:
            css_class = "danger"  # Red
        elif self.status == USERSTATUS_DELETED:
            css_class = "default disabled"  # Black
        return css_class

    @cached_property
    def age(self):
        today = timezone.now()
        return (
            today.year
            - self.birthdate.year
            - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        )

    @cached_property
    def iban_nice(self):
        if self.iban:
            value = self.iban
            # Code stolen from
            # https://django-localflavor.readthedocs.org/en/latest/_modules/localflavor/generic/forms/#IBANFormField.prepare_value
            grouping = 4
            value = value.upper().replace(" ", "").replace("-", "")
            return " ".join(
                value[i : i + grouping] for i in range(0, len(value), grouping)
            )
        return ""

    def formation_icon(self):
        return formation_short(self.formation)

    @cached_property
    def actor(self):
        return self.actor_for.exists()

    @cached_property
    def has_address(self):
        """
        Whether we have any address field set
        """
        address_fields = [
            f.name for f in Address._meta.get_fields() if f.name.startswith("address_")
        ]
        return any([getattr(self, field, False) != "" for field in address_fields])

    @cached_property
    def is_paid_staff(self):
        """
        Whether a UserProfile is probably a paid staff
        """
        return self.affiliation_canton

    @cached_property
    def actor_inline(self):
        return " - ".join([smart_text(a) for a in self.actor_for.all()])

    def actor_icon(self):
        if self.actor_inline:
            return mark_safe(
                STDGLYPHICON.format(icon="sunglasses", title=self.actor_inline)
            )
        return ""

    @cached_property
    def bagstatus_full(self):
        if self.bagstatus:
            return dict(BAGSTATUS_CHOICES)[self.bagstatus]
        return ""

    def bagstatus_icon(self):
        icon = ""
        title = self.bagstatus_full
        if self.bagstatus == BAGSTATUS_NONE:
            icon = "unchecked"
        elif self.bagstatus == BAGSTATUS_LOAN:
            icon = "new-window"
        elif self.bagstatus == BAGSTATUS_PAID or self.bagstatus == BAGSTATUS_GIFT:
            icon = "check"
        if icon:
            return mark_safe(STDGLYPHICON.format(icon=icon, title=title))
        return ""

    @cached_property
    def language_verb(self):
        try:
            return [c[1] for c in DV_LANGUAGES if c[0] == self.language][0]
        except IndexError:
            return ""

    def access_level(self, textonly=True):
        icon = ""
        title = ""
        if self.can_login:
            title = _("A accès")
            icon = "user"

            if self.user.is_superuser:
                title = _("Administra·teur·trice")
                icon = "queen"
            elif self.user.groups.exists():
                if has_role(self.user, "power_user"):
                    title = _("Super-utilisa·teur·trice")
                    icon = "king"
                elif has_role(self.user, "state_manager"):
                    title = _("Chargé·e de projet")
                    icon = "bishop"
                elif has_role(self.user, "coordinator"):
                    title = _("Coordina·teur·trice")
                    icon = "pawn"
                elif has_role(self.user, "collaborator"):
                    title = _("Collabora·teur·trice")
                    icon = "user"
        if title and textonly:
            return title
        if icon:
            return mark_safe(STDGLYPHICON.format(icon=icon, title=title))
        return ""

    @cached_property
    def access_level_icon(self):
        return self.access_level(False)

    @cached_property
    def access_level_text(self):
        return self.access_level(True)

    @cached_property
    def managed_cantons(self):
        return [m.canton for m in self.user.managedstates.all()]

    @cached_property
    def mailtolink(self):
        return "{name} <{email}>".format(
            name=self.user.get_full_name(), email=self.user.email
        )

    @cached_property
    def can_login(self):
        return self.user.is_active and self.user.has_usable_password()

    @memoize()
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
        if self.formation or self.actor:
            if self.affiliation_canton:
                usercantons += [self.affiliation_canton]
            if self.activity_cantons:
                usercantons += self.activity_cantons
            if not has_permission(self.user, "challenge_season_see_state_planning"):
                # PLANNING seasons are invisible for these
                qs = qs.exclude(state__in=[DV_SEASON_STATE_PLANNING,])

        # Unique'ify, discard empty values
        usercantons = set([c for c in usercantons if c])

        if usercantons:
            cantons_regexp = MULTISELECTFIELD_REGEXP % "|".join(usercantons)
            return qs.filter(cantons__regex=cantons_regexp)

        return qs.none()

    @cached_property
    def deleted(self):
        return (
            self.status == USERSTATUS_DELETED
            and not self.user.is_active
            and not self.user.email
            and not self.user.has_usable_password()
        )

    def send_mail(self, subject: str, body: str):
        """
        Send an email to that user
        """
        if self.user.email:
            return send_mail(
                subject, body, settings.DEFAULT_FROM_EMAIL, [self.mailtolink,],
            )

    def __str__(self):
        return self.user.get_full_name()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.id)

    class Meta:
        verbose_name = _("Profil")
        verbose_name_plural = _("Profils")


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def User_pre_save(sender, **kwargs):
    if not kwargs["instance"].username:
        kwargs["instance"].username = get_new_username()
        # Mark new users as inactive, to not let them get a login
        kwargs["instance"].is_active = False


class UserManagedState(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="managedstates",
        limit_choices_to={"is_active": True},
        on_delete=models.CASCADE,
    )
    canton = models.CharField(_("Canton"), max_length=5, choices=DV_STATE_CHOICES)

    @property
    def canton_full(self):
        return [c[1] for c in DV_STATE_CHOICES if c[0] == self.address_canton][0]

    def __str__(self):
        return _("{name} est chargé·e de projet pour le canton " "{canton}").format(
            name=self.user.get_full_name(), canton=self.canton
        )

    class Meta:
        verbose_name = _("Canton géré")
        verbose_name_plural = _("Cantons gérés")
        unique_together = (("user", "canton"),)
