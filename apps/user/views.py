# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015, 2016 Didier Raboud <me+defivelo@odyx.org>
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
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.forms import Form as DjangoEmptyForm
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
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
    DV_PRIVATE_FIELDS, DV_PUBLIC_FIELDS, FORMATION_CHOICES, PERSONAL_FIELDS,
    STD_PROFILE_FIELDS, USERSTATUS_ACTIVE, USERSTATUS_CHOICES,
    USERSTATUS_RESERVE, UserProfile,
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
            return reverse_lazy('profile-detail')
        return reverse_lazy('user-detail', kwargs={'pk': updatepk})

    def form_valid(self, form):
        ret = super(ProfileMixin, self).form_valid(form)
        """
        Write the non-model fields
        """
        user = self.get_object()
        if not user:
            user = self.object

        update_profile_fields = PERSONAL_FIELDS
        # if the edit user has access, extend the update_profile_fields
        if has_permission(self.request.user, 'user_crud_dv_public_fields'):
            update_profile_fields += DV_PUBLIC_FIELDS
        if has_permission(self.request.user, 'user_crud_dv_private_fields'):
            update_profile_fields += DV_PRIVATE_FIELDS

        (userprofile, created) = (
            UserProfile.objects.get_or_create(user=user)
        )
        for field in update_profile_fields:
            if field in form.cleaned_data:
                # For field updates that have date markers, note them properly
                if field in ['status', 'bagstatus']:
                    oldstatus = int(getattr(userprofile, field))
                    try:
                        newstatus = int(form.cleaned_data[field])
                    except ValueError:
                        newstatus = 0
                    if oldstatus != newstatus:
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

    def get_form_kwargs(self):
        kwargs = super(UserSelfAccessMixin, self).get_form_kwargs()
        if has_permission(self.request.user, self.required_permission):
            kwargs['allow_email'] = True
        return kwargs


class UserDetail(UserSelfAccessMixin, ProfileMixin, DetailView):
    required_permission = 'user_detail_other'

    def get_queryset(self):
        return (
            super(UserDetail, self).get_queryset()
            .prefetch_related('profile')
        )


class UserUpdate(UserSelfAccessMixin, ProfileMixin, SuccessMessageMixin,
                 UpdateView):
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
                 CreateView):
    required_permission = 'user_create'
    success_message = _("Utilisateur créé")

    def get_form_kwargs(self):
        kwargs = super(UserCreate, self).get_form_kwargs()
        kwargs['allow_email'] = True
        return kwargs

    def get_success_url(self):
        try:
            return reverse_lazy('user-detail', kwargs={'pk': self.object.pk})
        except:
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
        queryset=QualificationActivity.objects.filter(category='C')
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


class UserCredentials(ProfileMixin, FormView):
    template_name = 'auth/user_send_credentials.html'
    success_message = _("Données de connexion expédiées.")
    form_class = DjangoEmptyForm
    initial_send = True

    def get_context_data(self, **kwargs):
        context = super(UserCredentials, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['userprofile'] = self.get_object()
        context['current_site'] = Site.objects.get_current()
        context['login_uri'] = \
            self.request.build_absolute_uri(reverse('account_login'))
        context['initial_send'] = self.initial_send
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        context['fromuser'] = self.request.user
        user = self.get_object()
        user.profile.send_credentials(context, force=(not self.initial_send))
        return super(UserCredentials, self).form_valid(form)


class SendUserCredentials(HasPermissionsMixin, UserCredentials):
    required_permission = 'user_can_send_credentials'

    def dispatch(self, request, *args, **kwargs):
        # Forbid view if can already login
        if not self.get_object().profile.can_login:
            return (
                super(SendUserCredentials, self)
                .dispatch(request, *args, **kwargs)
            )
        else:
            raise PermissionDenied


class ResendUserCredentials(HasPermissionsMixin, UserCredentials):
    required_permission = 'user_can_resend_credentials'
    success_message = _("Données de connexion ré-expédiées.")
    initial_send = False

    def dispatch(self, request, *args, **kwargs):
        # Forbid view if initial login hasn't been sent
        if self.get_object().profile.can_login and not self.initial_send:
            return (
                super(ResendUserCredentials, self)
                .dispatch(request, *args, **kwargs)
            )
        else:
            raise PermissionDenied
