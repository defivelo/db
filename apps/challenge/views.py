# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.dates import WeekArchiveView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import QualificationForm, SessionForm
from .models import Qualification, Session


class SessionMixin(object):
    model = Session
    context_object_name = 'session'
    form_class = SessionForm

    def get_context_data(self, **kwargs):
        context = super(SessionMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'session'
        return context


class SessionsListView(SessionMixin, WeekArchiveView):
    date_field = "day"
    context_object_name = 'sessions'
    allow_empty = True
    allow_future = True
    week_format = '%W'
    ordering = ['day', 'timeslot__begin']


class SessionDetailView(SessionMixin, DetailView):
    def get_queryset(self):
        return (
            super(SessionDetailView, self).get_queryset()
            .prefetch_related(
                'organization',
                'timeslot',
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


class QualiMixin(SessionMixin):
    model = Qualification
    context_object_name = 'qualification'
    form_class = QualificationForm

    def get_session_id(self):
        resolvermatch = self.request.resolver_match
        if 'session' in resolvermatch.kwargs:
            return int(resolvermatch.kwargs['session'])

    def get_success_url(self):
        return reverse_lazy('session-detail', kwargs={'pk': self.get_session_id()})

    def get_context_data(self, **kwargs):
        context = super(QualiMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] += ' qualification'
        try:
            context['session'] = Session.objects.get(pk=self.get_session_id())
        except:
            pass
        return context


class QualiCreateView(QualiMixin, SuccessMessageMixin, CreateView):
    success_message = _("Qualification créée")

    def get_initial(self):
        return {'session': self.get_session_id()}


class QualiUpdateView(QualiMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Qualification mise à jour")


class QualiDeleteView(QualiMixin, DeleteView):
    success_message = _("Qualification supprimée")
