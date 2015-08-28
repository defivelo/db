# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import SessionForm
from .models import Session


class SessionsListView(ListView):
    model = Session
    context_object_name = 'sessions'

    def get_queryset(self):
        return Session.objects.filter(day__gte=timezone.now().date()).order_by('day')


class SessionDetailView(DetailView):
    model = Session
    context_object_name = 'session'


class SessionUpdateView(UpdateView):
    model = Session
    context_object_name = 'session'
    form_class = SessionForm


class SessionCreateView(CreateView):
    model = Session
    context_object_name = 'session'
    form_class = SessionForm


class SessionDeleteView(DeleteView):
    model = Session
    success_url = reverse_lazy('session-list')
