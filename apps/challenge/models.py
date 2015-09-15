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

MAX_MONO1_PER_QUALI = 2
DEFAULT_SESSION_DURATION_HOURS = 3
DEFAULT_EARLY_MINUTES_FOR_HELPERS_MEETINGS = 60


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


@python_2_unicode_compatible
class Session(Address, models.Model):
    created_on = models.DateTimeField(auto_now_add=True)

    # Time span
    day = models.DateField(_('Date'), blank=True)
    begin = models.TimeField(_('Début'), blank=True, null=True)
    duration = models.DurationField(_('Durée'),
                                    default=timedelta(
                                        hours=DEFAULT_SESSION_DURATION_HOURS
                                        ))
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
        unique_together = (('organization', 'begin', 'day'),)
        ordering = ['day', 'begin', 'organization__name']

    @property
    def errors(self):
        errors = []
        if not self.begin or not self.duration:
            errors.append(_('Horaire'))
        if not self.fallback_plan:
            errors.append(_('Mauvais temps'))
        if not self.apples:
            errors.append(_('Pommes'))
        # Check the qualifications
        qualiq = 0
        for quali in self.qualifications.all():
            qualiq += 1
            if quali.errors:
                errors.append(_('Quali : {name}').format(name=quali.name))
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

    @property
    def end(self):
        if self.begin and self.duration:
            day = self.day if self.day else datetime.today()
            end = datetime.combine(day, self.begin) + self.duration
            return end.time()

    def helpers_time_with_default(self):
        if self.helpers_time:
            return self.helpers_time
        if self.begin:
            # Compute a default value with regards to the start time
            helpers_time = (
                datetime.combine(datetime.today(), self.begin) -
                timedelta(minutes=DEFAULT_EARLY_MINUTES_FOR_HELPERS_MEETINGS)
                ).time().strftime('%H:%M')
            return mark_safe('<em>{}</em>'.format(helpers_time))
        return ''

    def __str__(self):
        return '{date}{begin}{orga}'.format(
            date=date(self.day, settings.DATE_FORMAT),
            begin=' (%s)' % self.begin if self.begin else '',
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
