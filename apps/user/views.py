# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from defivelo.views import MenuView

from .forms import UserProfileForm
from .models import UserProfile


class ProfileMixin(MenuView):
    model = get_user_model()
    context_object_name = 'userprofile'
    form_class = UserProfileForm
    profile_fields = ['address_street', 'address_no', 'address_zip',
                      'address_city', 'address_canton', 'natel', 'iban',
                      'social_security',
                      'formation', 'actor_for']

    def get_context_data(self, **kwargs):
        context = super(ProfileMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'user'
        return context

    def get_object(self):
        """
        Fallback to myself when accessing the profile
        """
        resolvermatch = self.request.resolver_match
        return self.model.objects.get(
            pk=int(resolvermatch.kwargs.get('pk', self.request.user.pk))
            )

    def get_success_url(self):
        if self.get_object().pk == self.request.user.pk:
            return reverse_lazy('profile-update')
        return reverse_lazy('user-list')

    def form_valid(self, form):
        ret = super(ProfileMixin, self).form_valid(form)
        """
        Write the non-model fields
        """
        user = self.get_object()
        if not user:
            user = self.object

        (userprofile, created) = (
            UserProfile.objects.get_or_create(user=user)
        )
        for field in self.profile_fields:
            if field in form.cleaned_data:
                setattr(userprofile, field, form.cleaned_data[field])
        userprofile.save()
        return ret


class UserDetail(ProfileMixin, DetailView):
    def get_queryset(self):
        return (
            super(SessionDetailView, self).get_queryset()
            .prefetch_related('profile')
        )


class UserUpdate(ProfileMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Profil mis à jour")

    def get_initial(self):
        """
        Pre-fill the form with the non-model fields
        """
        user = self.get_object()
        if hasattr(user, 'profile'):
            struct = {}
            for field in self.profile_fields:
                struct[field] = getattr(user.profile, field)
            return struct


class UserCreate(ProfileMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Utilisateur créé")

    def get_object(self):
        return None

    def get_success_url(self):
        return reverse_lazy('user-list')


class UserList(ProfileMixin, ListView):
    context_object_name = 'users'
    paginate_by = 10
    paginate_orphans = 3

    def get_queryset(self):
        return self.model.objects.order_by('first_name', 'last_name')


class UserDetailedList(UserList):
    context_object_name = 'users'
    template_name = 'auth/user_detailed_list.html'
    page_title = _('Liste des utilisateurs')

    def get_context_data(self, **kwargs):
        context = super(UserDetailedList, self).get_context_data(**kwargs)
        # Add our page title
        context['page_title'] = self.page_title
        return context

    def get_queryset(self):
        return (
            super(UserDetailedList, self).get_queryset()
            .prefetch_related('profile')
        )


class HelpersList(UserDetailedList):
    page_title = _('Liste des moniteurs')

    def get_queryset(self):
        return (
            super(HelpersList, self).get_queryset()
            .filter(profile__formation__in=['M1', 'M2'])
        )


class ActorsList(UserDetailedList):
    page_title = _('Liste des intervenants')

    def get_queryset(self):
        return (
            super(ActorsList, self).get_queryset()
            .exclude(profile__actor_for__isnull=True)
        )
