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

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import IntegerChoices, Q
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from parler.models import TranslatableModel, TranslatedFields
from sentry_sdk import capture_message as sentry_message
from sentry_sdk import configure_scope as sentry_scope
from simple_history.models import HistoricalRecords

from apps.salary.models import Timesheet
from apps.user import FORMATION_KEYS, FORMATION_M2

from .. import CHOSEN_AS_ACTOR, CHOSEN_AS_HELPER, CHOSEN_AS_LEADER
from .session import Session

# Using non-lazy translation to be exportable in XSL
CATEGORY_CHOICE_A = gettext("Agilité")
CATEGORY_CHOICE_B = gettext("Mécanique")
CATEGORY_CHOICE_C = gettext("Rencontre")

CATEGORY_CHOICES = (
    ("A", CATEGORY_CHOICE_A),
    ("B", CATEGORY_CHOICE_B),
    ("C", CATEGORY_CHOICE_C),
)


class QualificationActivity(TranslatableModel):
    translations = TranslatedFields(name=models.CharField(_("Nom"), max_length=255))
    category = models.CharField(
        _("Catégorie"), max_length=1, choices=CATEGORY_CHOICES, blank=True
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Poste")
        verbose_name_plural = _("Postes")
        ordering = ["category", "pk"]

    def __str__(self):
        return self.name


def num2words(number: int) -> str:
    num_map = {
        0: _("zéro"),
        1: _("un"),
        2: _("deux"),
        3: _("trois"),
    }
    return str(num_map.get(number, str(number)))


class MonitorNumberEnum(IntegerChoices):
    """
    Represente le nombre de moniteurs 1 et 2 pour une qualif.
    - Si nombre de moniteurs = 1 alors M1 = 0, M2 = 1
    - Si nombre de moniteurs = 2 alors M1 = 1, M2 = 1
    - Si nombre de moniteurs = 3 alors M1 = 2, M2 = 1
    """

    ONE = 1, "1"
    TWO = 2, "2"
    THREE = 3, "3"

    @property
    def m1(self) -> int:
        return max(0, self.value - 1)

    @property
    def m2(self) -> int:
        return 1


class Qualification(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    # TODO: Replace with automated or classes objects
    name = models.CharField(_("Nom de la classe"), max_length=255)
    session = models.ForeignKey(
        Session, related_name="qualifications", on_delete=models.CASCADE
    )
    class_teacher_fullname = models.CharField(
        _("Enseignant"), max_length=512, blank=True
    )
    class_teacher_natel = models.CharField(
        _("Natel enseignant"), max_length=13, blank=True
    )
    n_participants = models.PositiveSmallIntegerField(
        _("Nombre de participants"),
        blank=True,
        null=True,
        validators=[
            MaxValueValidator(30),
        ],
    )
    n_helpers = models.IntegerField(
        _("Nombre de moniteurs"),
        choices=MonitorNumberEnum.choices,
        default=MonitorNumberEnum.THREE,
    )

    n_bikes = models.PositiveSmallIntegerField(
        _("Nombre de vélos"),
        blank=True,
        null=True,
        validators=[
            MaxValueValidator(30),
        ],
    )
    n_helmets = models.PositiveSmallIntegerField(
        _("Nombre de casques"),
        blank=True,
        null=True,
        validators=[
            MaxValueValidator(30),
        ],
    )
    activity_A = models.ForeignKey(
        QualificationActivity,
        limit_choices_to={"category": "A"},
        verbose_name=CATEGORY_CHOICE_A,
        related_name="qualifs_A",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    activity_B = models.ForeignKey(
        QualificationActivity,
        limit_choices_to={"category": "B"},
        verbose_name=CATEGORY_CHOICE_B,
        related_name="qualifs_B",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    activity_C = models.ForeignKey(
        QualificationActivity,
        limit_choices_to={"category": "C"},
        verbose_name=CATEGORY_CHOICE_C,
        related_name="qualifs_C",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Moniteur 2"),
        related_name="qualifs_mon2",
        limit_choices_to=Q(profile__formation=FORMATION_M2),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    helpers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Moniteurs 1"),
        related_name="qualifs_mon1",
        limit_choices_to=Q(profile__formation__in=FORMATION_KEYS),
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Intervenant"),
        related_name="qualifs_actor",
        limit_choices_to={"profile__actor_for__isnull": False},
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    comments = models.TextField(_("Remarques"), blank=True)
    history = HistoricalRecords()

    @property
    def n_helpers_enum(self) -> MonitorNumberEnum:
        return MonitorNumberEnum(self.n_helpers)

    @cached_property
    def has_availability_incoherences(self):
        # Check les intervenants
        if (
            self.actor
            and not self.session.availability_statuses.filter(
                helper=self.actor, chosen_as=CHOSEN_AS_ACTOR
            ).exists()
        ):
            return True
        # Check les moniteurs 2
        if (
            self.leader
            and not self.session.availability_statuses.filter(
                helper=self.leader, chosen_as=CHOSEN_AS_LEADER
            ).exists()
        ):
            return True
        # Check les moniteurs 1
        for helper in self.helpers.all():
            if not self.session.availability_statuses.filter(
                helper=helper, chosen_as=CHOSEN_AS_HELPER
            ).exists():
                return True
        return False

    def fix_availability_incoherences(self):
        # many-to-many won't work without self.id.
        if not self.id:
            return

        # Check les intervenants
        if (
            self.actor
            and not self.session.availability_statuses.filter(
                helper=self.actor, chosen_as=CHOSEN_AS_ACTOR
            ).exists()
        ):
            self.actor = None
        # Check les moniteurs 2
        if (
            self.leader
            and not self.session.availability_statuses.filter(
                helper=self.leader, chosen_as=CHOSEN_AS_LEADER
            ).exists()
        ):
            self.leader = None
        # Check les moniteurs 1
        for helper in self.helpers.all():
            if not self.session.availability_statuses.filter(
                helper=helper, chosen_as=CHOSEN_AS_HELPER
            ).exists():
                self.helpers.remove(helper)

    def user_errors(self, user=None):
        errors = []
        if not self.class_teacher_fullname or not self.class_teacher_natel:
            errors.append(gettext("Enseignant"))
        if not self.n_participants:
            errors.append(gettext("Nombre de participants"))
        if self.session.orga.coordinator != user:
            if not self.leader or self.helpers.count() != self.n_helpers_enum.m1:
                errors.append(gettext("Moniteurs"))
            if not self.actor:
                errors.append(gettext("Intervenant"))
            if not self.activity_A or not self.activity_B or not self.activity_C:
                errors.append(gettext("Postes"))
            if self.has_availability_incoherences:
                errors.append(gettext("Incohérences de dispos"))
        if errors:
            return mark_safe(
                "<br />".join(
                    [
                        '<span class="btn-warning btn-xs disabled">'
                        '  <span class="glyphicon glyphicon-warning-sign"></span>'
                        " %s"
                        "</span>" % e
                        for e in errors
                    ]
                )
            )

    @property
    def errors(self):
        return self.user_errors(None)

    @classmethod
    def _get_label(cls, field):
        return str(cls._meta.get_field(field).verbose_name)

    @property
    def helpers_label(self):
        return self._get_label("helpers")

    @property
    def leader_label(self):
        return self._get_label("leader")

    @property
    def actor_label(self):
        return self._get_label("actor")

    def get_related_timesheets(self):
        # Do not distinct, so deletion is possible.
        # Requires distinct for display.
        return Timesheet.objects.filter(
            (
                Q(user__qualifs_actor=self)
                | Q(user__qualifs_mon2=self)
                | Q(user__qualifs_mon1=self)
            )
            & Q(date=self.session.day)
        )

    def save(self, *args, **kwargs):
        # Forcibly fix availability incoherences
        self.fix_availability_incoherences()
        with sentry_scope() as scope:
            scope.level = "info"
            scope.fingerprint = ["Qualification.save()"]
            scope.set_tag("Qualification", self)
            scope.set_tag("Qualification.id", self.id)

        sentry_message(
            "Qualification.save() : {quali}{mon2}".format(
                quali=self,
                mon2=" - Mon2: {leader} ({id})".format(
                    id=self.leader_id, leader=self.leader.get_full_name()
                )
                if self.leader
                else "",
            )
        )
        return super(Qualification, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Qualif’")
        verbose_name_plural = _("Qualifs")
        ordering = ["session", "created_on", "name"]

    def __str__(self):
        return "{name} ({session})".format(name=self.name, session=self.session)
