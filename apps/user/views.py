# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015 Didier Raboud <me+defivelo@odyx.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

import operator
from functools import reduce

from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django_filters import (
    CharFilter, FilterSet, ModelMultipleChoiceFilter, MultipleChoiceFilter,
)
from django_filters.views import FilterView
from filters.views import FilterMixin
from import_export.formats import base_formats
from rolepermissions.mixins import HasPermissionsMixin
from rolepermissions.verifications import has_permission

from apps.challenge.models import QualificationActivity
from apps.common import DV_STATE_CHOICES_WITH_DEFAULT
from defivelo.views import MenuView

from .export import UserResource
from .forms import UserProfileForm
from .models import (
    FORMATION_CHOICES, STD_PROFILE_FIELDS, USERSTATUS_ACTIVE,
    USERSTATUS_CHOICES, USERSTATUS_RESERVE, UserProfile,
)


class ProfileMixin(MenuView):
    model = get_user_model()
    context_object_name = 'userprofile'
    form_class = UserProfileForm
    profile_fields = STD_PROFILE_FIELDS

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
        updatepk = self.get_object().pk
        if updatepk == self.request.user.pk:
            return reverse_lazy('profile-update')
        return reverse_lazy('user-detail', kwargs={'pk': updatepk})

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
                # For field updates that have date markes, note them properly
                if field in ['status', 'bagstatus']:
                    oldstatus = getattr(userprofile, field)
                    if int(oldstatus) != int(form.cleaned_data[field]):
                        setattr(userprofile, '%s_updatetime' % field,
                                timezone.now()
                                )
                setattr(userprofile, field, form.cleaned_data[field])
        userprofile.save()
        return ret


class UserSelfAccessMixin(object):
    required_permission = 'user_edit_other'

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.pk == self.get_object().pk or
            has_permission(request.user, self.required_permission)
           ):
            return (
                super(UserSelfAccessMixin, self)
                .dispatch(request, *args, **kwargs)
            )
        else:
            raise PermissionDenied


class UserDetail(UserSelfAccessMixin, ProfileMixin, DetailView):
    required_permission = 'user_detail_other'

    def get_queryset(self):
        return (
            super(UserDetail, self).get_queryset()
            .prefetch_related('profile')
        )


class UserUpdate(UserSelfAccessMixin, ProfileMixin, SuccessMessageMixin,
                 UpdateView):
    required_permission = 'user_edit_other'
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


class UserCreate(HasPermissionsMixin, ProfileMixin, SuccessMessageMixin,
                 UpdateView):
    required_permission = 'user_create'
    success_message = _("Utilisateur créé")

    def get_object(self):
        return None

    def get_success_url(self):
        return reverse_lazy('user-list')


class UserProfileFilterSet(FilterSet):
    def filter_cantons(queryset, value):
        if value:
            allcantons_filter = [
                Q(profile__activity_cantons__contains=canton)
                for canton in value
            ] + [
                Q(profile__affiliation_canton=canton) for canton in value
            ]
            return queryset.filter(reduce(operator.or_, allcantons_filter))
        return queryset

    def filter_wide(queryset, value):
        if value:
            allfields_filter = [
                Q(last_name__icontains=value),
                Q(first_name__icontains=value),
                Q(email__icontains=value),
                Q(profile__natel__icontains=value)
            ]
            return queryset.filter(reduce(operator.or_, allfields_filter))
        return queryset

    profile__activity_cantons = MultipleChoiceFilter(
        label=_("Cantons"),
        choices=DV_STATE_CHOICES_WITH_DEFAULT,
        action=filter_cantons
    )
    profile__status = MultipleChoiceFilter(
        label=_('Statut'),
        choices=USERSTATUS_CHOICES,
        initial=[USERSTATUS_ACTIVE, USERSTATUS_RESERVE, ]
    )
    profile__formation = MultipleChoiceFilter(
        label=_('Formation'),
        choices=FORMATION_CHOICES
    )
    profile__actor_for = ModelMultipleChoiceFilter(
        label=_('Intervenant'),
        queryset=QualificationActivity.objects.all()
    )
    q = CharFilter(
        label=_('Recherche'),
        action=filter_wide
    )

    class Meta:
        model = get_user_model()
        fields = ['profile__status',
                  'profile__formation',
                  'profile__actor_for',
                  'profile__activity_cantons',
                  ]


class UserList(HasPermissionsMixin, ProfileMixin, FilterMixin, FilterView):
    required_permission = 'user_view_list'
    filterset_class = UserProfileFilterSet
    context_object_name = 'users'
    paginate_by = 10
    paginate_orphans = 3

    def get_context_data(self, *args, **kwargs):
        context = super(UserList, self).get_context_data(*args, **kwargs)
        # Re-create the filtered querystring from GET, drop page off it
        querydict = self.request.GET.copy()
        try:
            del querydict['page']
        except:
            pass
        context['filter_querystring'] = querydict.urlencode()
        return context

    def get_queryset(self):
        return (
            super(UserList, self).get_queryset()
            .prefetch_related('profile')
            .order_by('first_name', 'last_name')
        )


class UserListExport(UserList):
    def render_to_response(self, context, **response_kwargs):
        resolvermatch = self.request.resolver_match
        formattxt = resolvermatch.kwargs.get('format', 'csv')
        # Instantiate the format object from base_formats in import_export
        try:
            format = getattr(base_formats, formattxt.upper())()
        except AttributeError:
            format = base_formats.CSV()

        dataset = UserResource().export(self.object_list)

        filename = (
            _('DV-Utilisateurs-{YMD_date}.{extension}').format(
                YMD_date=timezone.now().strftime('%Y%m%d'),
                extension=format.get_extension()
            )
        )

        response = HttpResponse(getattr(dataset, formattxt),
                                format.get_content_type() + ';charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="{f}"'.format(
            f=filename)
        return response


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
