# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import date
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as u, ugettext_lazy as _

from apps.orga.models import Organization
from parler.models import TranslatableModel, TranslatedFields

MAX_MONO1_PER_QUALI = 2


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
    FALLBACK_CHOICES = (
        ('A', _('Programme déluge')),
        ('B', _('Annulation')),
        ('C', _('Report …')),
        ('D', _('Autre …')),
    )
    fallback_plan = models.CharField(_("Mauvais temps"), max_length=1,
                                     choices=FALLBACK_CHOICES, blank=True)
    helpers_time = models.TimeField(_('Heure rendez-vous moniteurs'),
                                    null=True, blank=True)
    helpers_place = models.CharField(_("Lieu rendez-vous moniteurs"),
                                     max_length=512, blank=True)
    apples = models.CharField(_("Pommes"), max_length=512, blank=True)
    comments = models.TextField(_('Remarques'), blank=True)

    class Meta:
        verbose_name = _('Session')
        verbose_name_plural = _('Sessions')
        unique_together = (('organization', 'timeslot', 'day'),)
        ordering = ['day', 'timeslot__begin', 'organization__name']

    def get_absolute_url(self):
        return reverse('session-detail', args=[self.pk])

    @property
    def errors(self):
        errors = []
        # Check the qualifications
        if not self.fallback_plan:
            errors.append(_('Mauvais temps'))
        if not self.apples:
            errors.append(_('Pommes'))
        qualiq = 0
        for quali in self.qualifications.all():
            qualiq += 1
            if quali.errors:
                errors.append(quali.name)
        if qualiq == 0:
            errors.append(_('Pas de qualifications'))
        if errors:
            return mark_safe(
                '<br />'.join(
                    [
                        '<span class="btn-warning btn-xs disabled">'
                        '  <span class="glyphicon glyphicon-warning-sign"></span>'
                        '  {error}'
                        '</span>'.format(error=e) for e in errors
                    ])
                )

    @property
    def fallback(self):
        if self.fallback_plan:
            return dict(self.FALLBACK_CHOICES)[self.fallback_plan]
        return ''

    def __str__(self):
        return '{date}{timeslot}{orga}'.format(
            date=date(self.day, settings.DATE_FORMAT),
            timeslot=' (%s)' % self.timeslot if self.timeslot else '',
            orga=' - %s' % self.organization.name if self.organization else ''
            )


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
    name = models.CharField(_('Nom'), max_length=255)  # TODO: Replace with automated or classes objects
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
                                   related_name='sessions_A',
                                   blank=True, null=True
                                   )
    activity_B = models.ForeignKey(QualificationActivity,
                                   limit_choices_to={'category': 'B'},
                                   verbose_name=_('Mécanique'),
                                   related_name='sessions_B',
                                   blank=True, null=True
                                   )
    activity_C = models.ForeignKey(QualificationActivity,
                                   limit_choices_to={'category': 'C'},
                                   verbose_name=_('Rencontre'),
                                   related_name='sessions_C',
                                   blank=True, null=True
                                   )
    leader = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('Moniteur 2'),
                               related_name='sessions_mon2',
                               limit_choices_to={'profile__formation': 'M2'},
                               blank=True, null=True)
    helpers = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                     verbose_name=_('Moniteurs 1'),
                                     related_name='sessions_mon1',
                                     limit_choices_to={
                                         'profile__formation__in': ['M1', 'M2']},
                                     blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,
                              verbose_name=_('Intervenant'),
                              related_name='sessions_actor',
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
