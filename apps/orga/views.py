# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import OrganizationForm
from .models import Organization


class OrganizationMixin:
    context_object_name = 'organization'
    def get_context_data(self, **kwargs):
        context = super(OrganizationMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'organization'
        return context


class OrganizationsListView(OrganizationMixin,ListView):
    model = Organization
    context_object_name = 'organizations'

    def get_queryset(self):
        return Organization.objects.all()


class OrganizationDetailView(OrganizationMixin,DetailView):
    model = Organization


class OrganizationUpdateView(OrganizationMixin,SuccessMessageMixin,UpdateView):
    model = Organization
    success_message = _("Établissement mis à jour")
    form_class = OrganizationForm


class OrganizationCreateView(OrganizationMixin,SuccessMessageMixin,CreateView):
    model = Organization
    success_message = _("Établissement créé")
    form_class = OrganizationForm


class OrganizationDeleteView(OrganizationMixin,DeleteView):
    model = Organization
    success_url = reverse_lazy('organization-list')
