# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016 Didier Raboud <me+defivelo@odyx.org>
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
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView

from django_filters import (
    CharFilter,
    FilterSet,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
)
from django_filters.views import FilterView
from rolepermissions.mixins import HasPermissionsMixin

from apps.challenge.models import QualificationActivity
from apps.common import (
    DV_LANGUAGES_WITH_DEFAULT,
    DV_STATE_CHOICES_WITH_DEFAULT,
    MULTISELECTFIELD_REGEXP,
)
from apps.common.views import ExportMixin, PaginatorMixin
from defivelo.roles import user_cantons

from .. import FORMATION_KEYS
from ..export import UserResource
from ..models import (
    FORMATION_CHOICES,
    USERSTATUS_ACTIVE,
    USERSTATUS_CHOICES,
    USERSTATUS_RESERVE,
    UserProfile,
)
from .mixins import ProfileMixin, UserSelfAccessMixin


class UserDetail(UserSelfAccessMixin, ProfileMixin, DetailView):
    required_permission = "user_detail_other"


class UserUpdate(UserSelfAccessMixin, ProfileMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Profil mis à jour")

    def get_initial(self):
        """
        Pre-fill the form with the non-model fields
        """
        userprofile = self.get_object()
        if hasattr(userprofile, "user"):
            struct = {}
            for field in ["email", "first_name", "last_name"]:
                struct[field] = getattr(userprofile.user, field)
            return struct

    def dispatch(self, request, *args, **kwargs):
        return super(UserUpdate, self).dispatch(request, *args, edit=True, **kwargs)


class UserCreate(HasPermissionsMixin, ProfileMixin, SuccessMessageMixin, CreateView):
    required_permission = "user_create"
    success_message = _("Utilisateur créé")

    def get_form_kwargs(self):
        kwargs = super(UserCreate, self).get_form_kwargs()
        kwargs["allow_email"] = True
        return kwargs

    def get_success_url(self):
        try:
            return reverse_lazy("user-detail", kwargs={"pk": self.object.user.pk})
        except Exception:
            return reverse_lazy("user-list")


class UserProfileFilterSet(FilterSet):
    def __init__(self, data=None, *args, **kwargs):
        cantons = kwargs.pop("cantons", None)
        if data is None or len(data) == 0:
            data = {}
            for name, f in self.base_filters.items():
                initial = f.extra.get("initial")
                # filter param is either missing or empty, use initial as default
                if not data.get(name) and initial:
                    data[name] = initial

        super(UserProfileFilterSet, self).__init__(data, *args, **kwargs)
        if cantons:
            if len(cantons) > 1:
                choices = self.filters["activity_cantons"].extra["choices"]
                choices = ((k, v) for (k, v) in choices if k in cantons or not k)
                self.filters["activity_cantons"].extra["choices"] = choices
            elif len(cantons) == 1:
                del self.filters["activity_cantons"]

    def filter_multi_nonempty(queryset, name, values):
        if values:
            allor_filter = [Q(**{name: v}) for v in values if v]
            if allor_filter:
                return queryset.filter(reduce(operator.or_, allor_filter))
        return queryset

    def filter_cantons(queryset, name, values):
        if values and any(values):
            # S'il y au moins un canton en commun
            cantons_regexp = MULTISELECTFIELD_REGEXP % "|".join(
                [v for v in values if v]
            )
            allcantons_filter = [Q(activity_cantons__regex=cantons_regexp)] + [
                Q(affiliation_canton=v) for v in values if v
            ]
            return queryset.filter(reduce(operator.or_, allcantons_filter))
        return queryset

    def filter_languages(queryset, name, values):
        if values and any(values):
            # S'il y au moins une langue en commun
            lang_regexp = MULTISELECTFIELD_REGEXP % "|".join([v for v in values if v])
            alllangs_filter = [Q(languages_challenges__regex=lang_regexp)] + [
                Q(language=v) for v in values if v
            ]
            return queryset.filter(reduce(operator.or_, alllangs_filter))
        return queryset

    def filter_wide(queryset, name, value):
        if value:
            allfields_filter = [
                Q(user__last_name__unaccent__icontains=value),
                Q(user__first_name__unaccent__icontains=value),
                Q(user__email__icontains=value),
                Q(natel__icontains=value),
            ]
            return queryset.filter(reduce(operator.or_, allfields_filter))
        return queryset

    language = MultipleChoiceFilter(
        label=_("Langue"),
        choices=DV_LANGUAGES_WITH_DEFAULT,
        method=filter_multi_nonempty,
    )

    languages_challenges = MultipleChoiceFilter(
        label=_("Langues d'animation"),
        choices=DV_LANGUAGES_WITH_DEFAULT,
        method=filter_languages,
    )

    affiliation_canton = MultipleChoiceFilter(
        label=_("Canton d'affiliation"),
        choices=DV_STATE_CHOICES_WITH_DEFAULT,
        method=filter_multi_nonempty,
    )

    activity_cantons = MultipleChoiceFilter(
        label=_("Cantons"), choices=DV_STATE_CHOICES_WITH_DEFAULT, method=filter_cantons
    )
    status = MultipleChoiceFilter(
        label=_("Statut"),
        choices=USERSTATUS_CHOICES,
        initial=[USERSTATUS_ACTIVE, USERSTATUS_RESERVE,],
    )
    formation = MultipleChoiceFilter(
        label=_("Formation"), choices=FORMATION_CHOICES, method=filter_multi_nonempty
    )
    actor_for = ModelMultipleChoiceFilter(
        label=_("Intervenant"),
        queryset=(
            QualificationActivity.objects.filter(category="C").prefetch_related(
                "translations"
            )
        ),
    )
    q = CharFilter(label=_("Recherche"), method=filter_wide)

    class Meta:
        model = UserProfile
        fields = [
            "status",
            "formation",
            "actor_for",
            "activity_cantons",
        ]


class UserList(HasPermissionsMixin, ProfileMixin, PaginatorMixin, FilterView):
    required_permission = "user_view_list"
    filterset_class = UserProfileFilterSet
    context_object_name = "profiles"

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super(UserList, self).get_filterset_kwargs(filterset_class)
        usercantons = user_cantons(self.request.user)
        if usercantons:
            kwargs["cantons"] = usercantons
        return kwargs


class UserListExport(ExportMixin, UserList):
    export_class = UserResource()
    export_filename = _("Utilisateurs")


class UserDetailedList(UserList):
    paginate_by = None
    context_object_name = "users"
    template_name = "auth/user_detailed_list.html"
    page_title = _("Liste des utilisateurs")

    def get_context_data(self, **kwargs):
        context = super(UserDetailedList, self).get_context_data(**kwargs)
        # Add our page title
        context["page_title"] = self.page_title
        return context


class HelpersList(UserDetailedList):
    page_title = _("Liste des moniteurs")

    def get_queryset(self):
        return (
            super(HelpersList, self).get_queryset().filter(formation__in=FORMATION_KEYS)
        )


class ActorsList(UserDetailedList):
    page_title = _("Liste des intervenants")

    def get_queryset(self):
        return super(ActorsList, self).get_queryset().exclude(_actor_for__isnull=True)

