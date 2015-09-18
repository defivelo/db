# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.dates import WeekArchiveView, YearArchiveView
from django.views.generic.detail import (
    DetailView, SingleObjectMixin, SingleObjectTemplateResponseMixin,
)
from django.views.generic.edit import (
    CreateView, DeleteView, FormView, UpdateView,
)
from django.views.generic.list import ListView

from defivelo.views import MenuView

from .forms import (
    QualificationForm, SeasonAvailabilityForm, SeasonForm, SessionForm,
)
from .models import HelperSessionAvailability, Qualification, Season, Session

AVAILABILITY_FIELDKEY = 'avail-h{hpk}-s{spk}'


class SeasonMixin(MenuView):
    model = Season
    context_object_name = 'season'
    form_class = SeasonForm

    def get_context_data(self, **kwargs):
        context = super(SeasonMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'season'
        return context


class SeasonListView(SeasonMixin, YearArchiveView):
    date_field = 'begin'
    allow_empty = True
    allow_future = True
    context_object_name = 'seasons'
    make_object_list = True
    pass


class SeasonDetailView(SeasonMixin, DetailView):
    pass


class SeasonUpdateView(SeasonMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Saison mise à jour")


class SeasonAvailabilityView(SeasonUpdateView):
    template_name = 'challenge/season_availability.html'
    success_message = _("Disponibilités mises à jour")
    form_class = SeasonAvailabilityForm

    def potential_helpers(self):
        all_helpers = get_user_model().objects
        return (
            (_('Moniteurs 2'), all_helpers.filter(profile__formation='M2')),
            (_('Moniteurs 1'), all_helpers.filter(profile__formation='M1')),
            (_('Intervenants'), all_helpers.exclude(profile__actor_for__isnull=True)),
        )

    def get_context_data(self, **kwargs):
        context = super(SeasonAvailabilityView, self).get_context_data(**kwargs)
        context['potential_helpers'] = self.potential_helpers()
        return context

    def get_initial(self):
        initials = {}
        all_hsas = HelperSessionAvailability.objects.filter(
            session__in=self.object.sessions)
        if all_hsas:
            for session in self.object.sessions:
                for helper_category, helpers in self.potential_helpers():
                    for helper in helpers:
                        fieldkey = AVAILABILITY_FIELDKEY.format(hpk=helper.pk,
                                                                spk=session.pk)
                        availability = [a.availability for a in all_hsas if a.helper == helper][0]
                        if availability:
                            initials[fieldkey] = availability
            return initials

    def form_valid(self, form):
        # Create or update the Availability objects
        for session in self.object.sessions:
            for helper_category, helpers in self.potential_helpers():
                for helper in helpers:
                    fieldkey = AVAILABILITY_FIELDKEY.format(hpk=helper.pk,
                                                            spk=session.pk)
                    if fieldkey in form.cleaned_data:
                        availability = form.cleaned_data[fieldkey]
                        (hsa, created) = (
                            HelperSessionAvailability.objects.get_or_create(
                                session=session,
                                helper=helper,
                                defaults={'availability': availability})
                            )
                        if not created:
                            hsa.availability = availability
                            hsa.save()
        return HttpResponseRedirect(reverse_lazy('season-detail',
                                                 kwargs={'pk': self.object.pk}))


class SeasonCreateView(SeasonMixin, SuccessMessageMixin, CreateView):
    success_message = _("Saison créée")


class SeasonDeleteView(SeasonMixin, SuccessMessageMixin, DeleteView):
    success_message = _("Saison supprimée")
    success_url = reverse_lazy('season-list')


class SessionMixin(MenuView):
    model = Session
    context_object_name = 'session'
    form_class = SessionForm

    def get_season(self):
        if not hasattr(self, 'season'):
            self.season = Season.objects.get(pk=int(self.kwargs['seasonpk']))
        return self.season

    def get_queryset(self):
        try:
            return self.model.objects.filter(
                organization__address_canton__in=self.get_season().cantons
                )
        except:
            return self.model.objects

    def get_success_url(self):
        return reverse_lazy('session-detail',
                            kwargs={
                                'seasonpk': self.get_season().pk,
                                'pk': self.object.pk
                                })

    def get_context_data(self, **kwargs):
        context = super(SessionMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'season'
        context['season'] = self.get_season()
        return context


class SessionsListView(SessionMixin, WeekArchiveView):
    date_field = "day"
    context_object_name = 'sessions'
    allow_empty = True
    allow_future = True
    week_format = '%W'
    ordering = ['day', 'begin', 'duration']


class SessionDetailView(SessionMixin, DetailView):
    def get_queryset(self):
        return (
            super(SessionDetailView, self).get_queryset()
            .prefetch_related(
                'organization',
                'qualifications',
                'qualifications__leader',
                'qualifications__leader__profile',
                'qualifications__helpers',
                'qualifications__helpers__profile',
                'qualifications__actor',
                'qualifications__actor__profile',
                'qualifications__activity_A',
                'qualifications__activity_B',
                'qualifications__activity_C')
        )


class SessionUpdateView(SessionMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Session mise à jour")


class SessionCreateView(SessionMixin, SuccessMessageMixin, CreateView):
    success_message = _("Session créée")


class SessionDeleteView(SessionMixin, SuccessMessageMixin, DeleteView):
    success_message = _("Session supprimée")
    success_url = reverse_lazy('session-list')


class SessionAvailabilityView(SessionDetailView):
    template_name = 'challenge/session_availability.html'


class QualiMixin(SessionMixin):
    model = Qualification
    context_object_name = 'qualification'
    form_class = QualificationForm

    def get_session_pk(self):
        resolvermatch = self.request.resolver_match
        if 'sessionpk' in resolvermatch.kwargs:
            return int(resolvermatch.kwargs['sessionpk'])

    def get_season_pk(self):
        resolvermatch = self.request.resolver_match
        if 'seasonpk' in resolvermatch.kwargs:
            return int(resolvermatch.kwargs['seasonpk'])

    def get_success_url(self):
        return reverse_lazy('session-detail', kwargs={
            'seasonpk': self.get_season_pk(),
            'pk': self.get_session_pk()
            })

    def get_context_data(self, **kwargs):
        context = super(QualiMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] += ' qualification'
        try:
            context['session'] = Session.objects.get(pk=self.get_session_pk())
        except:
            pass
        try:
            context['season'] = Season.objects.get(pk=self.get_season_pk())
        except:
            pass
        return context


class QualiCreateView(QualiMixin, SuccessMessageMixin, CreateView):
    success_message = _("Qualification créée")

    def get_initial(self):
        return {'session': self.get_session_pk()}


class QualiUpdateView(QualiMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Qualification mise à jour")


class QualiDeleteView(QualiMixin, DeleteView):
    success_message = _("Qualification supprimée")
