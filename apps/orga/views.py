# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from defivelo.views import MenuView

from .forms import OrganizationForm
from .models import Organization


class OrganizationMixin(MenuView):
    model = Organization
    context_object_name = 'organization'
    form_class = OrganizationForm

    def get_context_data(self, **kwargs):
        context = super(OrganizationMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'organization'
        return context


class OrganizationsListView(OrganizationMixin,
                            ListView):
    context_object_name = 'organizations'

    def get_queryset(self):
        return Organization.objects.all()


class OrganizationDetailView(OrganizationMixin,
                             DetailView):
    pass


class OrganizationUpdateView(OrganizationMixin,
                             SuccessMessageMixin,
                             UpdateView):
    success_message = _("Établissement mis à jour")


class OrganizationCreateView(OrganizationMixin,
                             SuccessMessageMixin,
                             CreateView):
    success_message = _("Établissement créé")


class OrganizationDeleteView(OrganizationMixin, DeleteView):
    success_url = reverse_lazy('organization-list')
