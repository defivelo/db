# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import date
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as u, ugettext_lazy as _
from multiselectfield import MultiSelectField

from apps.common.models import Address
from apps.orga.models import Organization
from localflavor.ch.ch_states import STATE_CHOICES
from parler.models import TranslatableModel, TranslatedFields

from .. import MAX_MONO1_PER_QUALI
from .session import Session


@python_2_unicode_compatible
class QualificationActivity(TranslatableModel):
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
    name = models.CharField(_('Nom de la classe'), max_length=255)  # TODO: Replace with automated or classes objects
    session = models.ForeignKey(Session,
                                related_name='qualifications')
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
                                   verbose_name=_('Vélo dans la rue'),
                                   related_name='qualifs_A',
                                   blank=True, null=True
                                   )
    activity_B = models.ForeignKey(QualificationActivity,
                                   limit_choices_to={'category': 'B'},
                                   verbose_name=_('Mécanique'),
                                   related_name='qualifs_B',
                                   blank=True, null=True
                                   )
    activity_C = models.ForeignKey(QualificationActivity,
                                   limit_choices_to={'category': 'C'},
                                   verbose_name=_('Rencontre'),
                                   related_name='qualifs_C',
                                   blank=True, null=True
                                   )
    leader = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('Moniteur 2'),
                               related_name='qualifs_mon2',
                               limit_choices_to={'profile__formation': 'M2'},
                               blank=True, null=True)
    helpers = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                     verbose_name=_('Moniteurs 1'),
                                     related_name='qualifs_mon1',
                                     limit_choices_to={
                                         'profile__formation__in': ['M1', 'M2']},
                                     blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,
                              verbose_name=_('Intervenant'),
                              related_name='qualifs_actor',
                              limit_choices_to={
                                  'profile__actor_for__isnull': False
                              },
                              blank=True, null=True)
    ROUTE_CHOICES = (
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    )
    route = models.CharField(_("Parcours"), max_length=1,
                             choices=ROUTE_CHOICES, blank=True)
    comments = models.TextField(_('Remarques'), blank=True)

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
                '<br />'.join(['<span class="btn-warning btn-xs disabled"><span class="glyphicon glyphicon-warning-sign"></span> %s</span>' % e for e in errors])
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
