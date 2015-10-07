# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

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
    CreateView, DeleteView, FormMixin, FormView, UpdateView,
)
from django.views.generic.list import ListView

from apps.user.views import ActorsList, HelpersList
from defivelo.views import MenuView

from .forms import (
    QualificationForm, SeasonAvailabilityForm, SeasonForm,
    SeasonNewHelperAvailabilityForm, SeasonStaffChoiceForm, SessionForm,
)
from .models import HelperSessionAvailability, Qualification, Season, Session

AVAILABILITY_FIELDKEY = 'avail-h{hpk}-s{spk}'
STAFF_FIELDKEY = 'staff-h{hpk}-s{spk}'


class SeasonMixin(MenuView):
    model = Season
    context_object_name = 'season'
    form_class = SeasonForm

    def get_season(self):
        if not hasattr(self, 'season'):
            try:
                self.season = Season.objects.get(pk=int(self.kwargs['pk']))
            except KeyError:
                self.season = None
        return self.season

    def get_context_data(self, **kwargs):
        context = super(SeasonMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'season'
        context['season'] = self.get_season()
        return context


class SeasonListView(SeasonMixin, YearArchiveView):
    date_field = 'begin'
    allow_empty = True
    allow_future = True
    context_object_name = 'seasons'
    make_object_list = True


class SeasonDetailView(SeasonMixin, DetailView):
    def get_context_data(self, **kwargs):
        context = super(SeasonDetailView, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context['submenu_category'] = 'season-detail'
        return context


class SeasonUpdateView(SeasonMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Saison mise à jour")


class SeasonAvailabilityMixin(SeasonMixin):
    def potential_helpers(self, queryset=None):
        if not queryset:
            queryset = get_user_model().objects

            # Pick the one helper from the command line if it makes sense
            resolvermatch = self.request.resolver_match
            if 'helperpk' in resolvermatch.kwargs:
                queryset = queryset.filter(
                    pk=int(resolvermatch.kwargs['helperpk'])
                )

        all_helpers = queryset.order_by('first_name', 'last_name')
        return (
            (_('Moniteurs 2'), all_helpers.filter(profile__formation='M2')),
            (_('Moniteurs 1'), all_helpers.filter(profile__formation='M1')),
            (_('Intervenants'), all_helpers.exclude(
                profile__actor_for__isnull=True
            )),
        )

    def current_availabilities(self):
        return (
            HelperSessionAvailability.objects
            .filter(session__in=self.object.sessions_with_qualifs)
            .prefetch_related('helper')
        )

    def get_initial(self, all_hsas=None, all_helpers=None):
        initials = OrderedDict()
        if not all_hsas:
            all_hsas = self.current_availabilities()
        if not all_helpers:
            all_helpers = self.potential_helpers()

        if all_hsas:
            for helper_category, helpers in all_helpers:
                for helper in helpers:
                    helper_availability = {
                        a.session_id: (a.availability, a.chosen) for a in all_hsas
                        if a.helper == helper
                    }
                    for session in self.object.sessions_with_qualifs:
                        fieldkey = AVAILABILITY_FIELDKEY.format(
                            hpk=helper.pk, spk=session.pk)
                        try:
                            initials[fieldkey] = (
                                helper_availability[session.id][0]
                            )
                            initials[STAFF_FIELDKEY.format(
                                hpk=helper.pk, spk=session.pk)] = (
                                helper_availability[session.id][1]
                            )
                        except:
                            initials[fieldkey] = ''
                            initials[STAFF_FIELDKEY.format(
                                hpk=helper.pk, spk=session.pk)] = False
            return initials

    def get_context_data(self, **kwargs):
        context = super(SeasonAvailabilityMixin, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context['submenu_category'] = 'season-availability'
        return context


class SeasonAvailabilityView(SeasonAvailabilityMixin, DetailView):
    template_name = 'challenge/season_availability.html'

    def get_context_data(self, **kwargs):
        context = super(SeasonAvailabilityView, self).get_context_data(**kwargs)
        # Add the form for picking a new helper
        context['form'] = SeasonNewHelperAvailabilityForm()
        hsas = self.current_availabilities()
        if hsas:
            # Fill in the helpers with the ones we currently have
            helpers = {hsa.helper.pk: hsa.helper.pk for hsa in hsas}
            potential_helpers = self.potential_helpers(
                queryset=get_user_model().objects.filter(pk__in=helpers)
            )

            context['potential_helpers'] = potential_helpers
            context['availabilities'] = self.get_initial(
                all_hsas=hsas,
                all_helpers=potential_helpers
            )
        return context

    def post(self, request, *args, **kwargs):
        seasonpk = kwargs.get('pk', None)
        form = SeasonNewHelperAvailabilityForm(request.POST)
        if form.is_valid():
            helperpk = int(form.cleaned_data['helper'])
            return HttpResponseRedirect(
                reverse_lazy('season-availabilities-update',
                             kwargs={'pk': seasonpk, 'helperpk': helperpk})
            )
        return HttpResponseRedirect(
            reverse_lazy('season-availabilities', kwargs={'pk': seasonpk})
        )


class SeasonAvailabilityUpdateView(SeasonAvailabilityMixin, SeasonUpdateView):
    template_name = 'challenge/season_availability_update.html'
    success_message = _("Disponibilités mises à jour")
    form_class = SeasonAvailabilityForm

    def get_form_kwargs(self):
        form_kwargs = super(SeasonAvailabilityMixin, self).get_form_kwargs()
        form_kwargs['potential_helpers'] = self.potential_helpers()
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super(SeasonAvailabilityMixin, self).get_context_data(**kwargs)
        context['potential_helpers'] = self.potential_helpers()
        return context

    def form_valid(self, form):
        # Create or update the Availability objects
        for session in self.object.sessions_with_qualifs:
            for helper_category, helpers in self.potential_helpers():
                for helper in helpers:
                    fieldkey = AVAILABILITY_FIELDKEY.format(hpk=helper.pk,
                                                            spk=session.pk)
                    if fieldkey in form.cleaned_data:
                        availability = form.cleaned_data[fieldkey]
                        if availability:
                            (hsa, created) = (
                                HelperSessionAvailability.objects.get_or_create(
                                    session=session,
                                    helper=helper,
                                    defaults={'availability': availability})
                                )
                            if not created:
                                hsa.availability = availability
                                hsa.save()
        return HttpResponseRedirect(reverse_lazy('season-availabilities',
                                                 kwargs={'pk': self.object.pk}))


class SeasonStaffChoiceUpdateView(SeasonAvailabilityMixin, SeasonUpdateView):
    template_name = 'challenge/season_staff_update.html'
    success_message = _("Choix du personnel mises à jour")
    form_class = SeasonStaffChoiceForm

    def available_helpers(self):
        if hasattr(self, 'ahelpers'):
            return self.ahelpers
        # Only take available people
        hsas = self.current_availabilities().exclude(availability='n')
        if hsas:
            # Fill in the helpers with the ones we currently have
            helpers = {hsa.helper.pk: hsa.helper.pk for hsa in hsas}
            self.ahelpers = self.potential_helpers(
                queryset=get_user_model().objects.filter(pk__in=helpers)
            )
            return self.ahelpers

    def get_form_kwargs(self):
        form_kwargs = super(SeasonStaffChoiceUpdateView, self).get_form_kwargs()
        form_kwargs['available_helpers'] = self.available_helpers()
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super(SeasonStaffChoiceUpdateView, self).get_context_data(**kwargs)
        context['available_helpers'] = self.available_helpers()
        return context

    def form_valid(self, form):
        # Update all staff choices
        for session in self.object.sessions_with_qualifs:
            for helper_category, helpers in self.available_helpers():
                for helper in helpers:
                    fieldkey = STAFF_FIELDKEY.format(hpk=helper.pk,
                                                     spk=session.pk)
                    try:
                        HelperSessionAvailability.objects.filter(
                                session=session,
                                helper=helper
                            ).update(chosen=form.cleaned_data[fieldkey])
                    except:  # if the fieldkey's not in cleaned_data, or other reasons
                        pass
        return HttpResponseRedirect(reverse_lazy('season-staff-update',
                                                 kwargs={'pk': self.object.pk}))


class SeasonCreateView(SeasonMixin, SuccessMessageMixin, CreateView):
    success_message = _("Saison créée")


class SeasonDeleteView(SeasonMixin, SuccessMessageMixin, DeleteView):
    success_message = _("Saison supprimée")
    success_url = reverse_lazy('season-list')


class SeasonHelperListView(HelpersList, SeasonMixin):
    page_title = _('Moniteurs de la saison')

    def get_context_data(self, **kwargs):
        context = super(SeasonHelperListView, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context['submenu_category'] = 'season-helperlist'
        return context

    def get_queryset(self):
        season = self.get_season()
        return (
            super(SeasonHelperListView, self).get_queryset()
            .filter(availabilities__session__in=season.sessions_with_qualifs,
                    availabilities__chosen=True)
            .distinct()
        )


class SeasonActorListView(ActorsList, SeasonMixin):
    page_title = _('Intervenants de la saison')

    def get_context_data(self, **kwargs):
        context = super(SeasonActorListView, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context['submenu_category'] = 'season-actorslist'
        return context

    def get_queryset(self):
        season = self.get_season()
        return (
            super(SeasonActorListView, self).get_queryset()
            .filter(availabilities__session__in=season.sessions_with_qualifs,
                    availabilities__chosen=True)
            .distinct()
        )


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
