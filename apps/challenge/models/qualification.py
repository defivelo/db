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

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as u, ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from sentry_sdk import capture_message as sentry_message
from simple_history.models import HistoricalRecords

from apps.user import FORMATION_KEYS, FORMATION_M2

from .. import MAX_MONO1_PER_QUALI
from .session import Session

CATEGORY_CHOICE_A = u('Agilité')
CATEGORY_CHOICE_B = u('Mécanique')
CATEGORY_CHOICE_C = u('Rencontre')

CATEGORY_CHOICES = (
    ('A', CATEGORY_CHOICE_A),
    ('B', CATEGORY_CHOICE_B),
    ('C', CATEGORY_CHOICE_C),
)


@python_2_unicode_compatible
class QualificationActivity(TranslatableModel):

    translations = TranslatedFields(
        name=models.CharField(_('Nom'), max_length=255)
    )
    category = models.CharField(_("Catégorie"), max_length=1,
                                choices=CATEGORY_CHOICES, blank=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Poste')
        verbose_name_plural = _('Postes')
        ordering = ['category', 'pk']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Qualification(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    # TODO: Replace with automated or classes objects
    name = models.CharField(_('Nom de la classe'), max_length=255)
    session = models.ForeignKey(Session,
                                related_name='qualifications',
                                on_delete=models.CASCADE)
    class_teacher_fullname = models.CharField(_('Enseignant'), max_length=512,
                                              blank=True)
    class_teacher_natel = models.CharField(_('Natel enseignant'),
                                           max_length=13, blank=True)
    n_participants = models.PositiveSmallIntegerField(
        _('Nombre de participants'),
        blank=True, null=True)
    n_bikes = models.PositiveSmallIntegerField(
        _('Nombre de vélos'),
        blank=True, null=True)
    n_helmets = models.PositiveSmallIntegerField(
        _('Nombre de casques'),
        blank=True, null=True)
    activity_A = models.ForeignKey(QualificationActivity,
                                   limit_choices_to={'category': 'A'},
                                   verbose_name=CATEGORY_CHOICE_A,
                                   related_name='qualifs_A',
                                   blank=True, null=True,
                                   on_delete=models.SET_NULL
                                   )
    activity_B = models.ForeignKey(QualificationActivity,
                                   limit_choices_to={'category': 'B'},
                                   verbose_name=CATEGORY_CHOICE_B,
                                   related_name='qualifs_B',
                                   blank=True, null=True,
                                   on_delete=models.SET_NULL
                                   )
    activity_C = models.ForeignKey(QualificationActivity,
                                   limit_choices_to={'category': 'C'},
                                   verbose_name=CATEGORY_CHOICE_C,
                                   related_name='qualifs_C',
                                   blank=True, null=True,
                                   on_delete=models.SET_NULL
                                   )
    leader = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('Moniteur 2'),
                               related_name='qualifs_mon2',
                               limit_choices_to=Q(
                                   profile__formation=FORMATION_M2
                                   ),
                               blank=True, null=True,
                               on_delete=models.SET_NULL)
    helpers = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                     verbose_name=_('Moniteurs 1'),
                                     related_name='qualifs_mon1',
                                     limit_choices_to=Q(
                                         profile__formation__in=FORMATION_KEYS
                                         ),
                                     blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,
                              verbose_name=_('Intervenant'),
                              related_name='qualifs_actor',
                              limit_choices_to={
                                  'profile__actor_for__isnull': False
                              },
                              blank=True, null=True,
                              on_delete=models.SET_NULL)
    comments = models.TextField(_('Remarques'), blank=True)
    history = HistoricalRecords()

    @property
    def errors(self):
        errors = []
        if not self.class_teacher_fullname or not self.class_teacher_natel:
            errors.append(u("Enseignant"))
        if not self.n_participants:
            errors.append(u("Nombre de participants"))
        if not self.leader or self.helpers.count() != MAX_MONO1_PER_QUALI:
            errors.append(u("Moniteurs"))
        if not self.actor:
            errors.append(u("Intervenant"))
        if not self.activity_A or not self.activity_B or not self.activity_C:
            errors.append(u('Postes'))
        if errors:
            return mark_safe(
                '<br />'.join([
                    '<span class="btn-warning btn-xs disabled">'
                    '  <span class="glyphicon glyphicon-warning-sign"></span>'
                    ' %s'
                    '</span>' % e for e in errors])
                )

    def save(self, *args, **kwargs):
        sentry_message(
            'Qualification.save() : {quali}{mon2}'
            .format(
                quali=self,
                mon2=' - Mon2: {leader} ({id})'.format(
                    id=self.leader_id,
                    leader=self.leader.get_full_name()
                ) if self.leader else ''
            )
        )
        return super(Qualification, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Qualif'")
        verbose_name_plural = _('Qualifs')
        ordering = ['session', 'created_on', 'name']

    def __str__(self):
        return '{name} ({session})'.format(
            name=self.name,
            session=self.session
            )
