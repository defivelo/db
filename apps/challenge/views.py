# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import SessionForm
from .models import Session


class SessionMixin:
    def get_context_data(self, **kwargs):
        context = super(SessionMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'session'
        return context


class SessionsListView(SessionMixin,ListView):
    model = Session
    context_object_name = 'sessions'

    def get_queryset(self):
        return Session.objects.filter(day__gte=timezone.now().date())


class SessionDetailView(SessionMixin,DetailView):
    model = Session
    context_object_name = 'session'


class SessionUpdateView(SessionMixin,SuccessMessageMixin,UpdateView):
    model = Session
    context_object_name = 'session'
    success_message = _("Session mise à jour")
    form_class = SessionForm


class SessionCreateView(SessionMixin,SuccessMessageMixin,CreateView):
    model = Session
    context_object_name = 'session'
    success_message = _("Session créée")
    form_class = SessionForm


class SessionDeleteView(SessionMixin,DeleteView):
    model = Session
    success_url = reverse_lazy('session-list')
