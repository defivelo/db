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
import operator
from functools import reduce

from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView

from django_filters import (
    CharFilter,
    FilterSet,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
)
from django_filters.views import FilterView
from rolepermissions.checkers import has_role
from rolepermissions.mixins import HasPermissionsMixin

from apps.challenge.models import QualificationActivity
from apps.common import DV_LANGUAGES_WITH_DEFAULT, DV_STATE_CHOICES_WITH_DEFAULT
from apps.common.views import ExportMixin, PaginatorMixin
from defivelo.roles import DV_AVAILABLE_ROLES, has_permission, user_cantons

from .. import FORMATION_KEYS
from ..export import CollaboratorUserResource, UserResource
from ..forms import SwissDateFilter
from ..models import (
    FORMATION_CHOICES,
    USERSTATUS_ACTIVE,
    USERSTATUS_ARCHIVE,
    USERSTATUS_CHOICES,
    USERSTATUS_DELETED,
    USERSTATUS_RESERVE,
)
from .mixins import ProfileMixin, UserSelfAccessMixin


def get_return_url(request):
    return_url = request.GET.get("returnUrl") or request.POST.get("returnUrl")
    if return_url and url_has_allowed_host_and_scheme(
        url=return_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return return_url
    return None


class UserDetail(UserSelfAccessMixin, ProfileMixin, DetailView):
    required_permission = "user_detail_other"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            managed_cantons = user_cantons(self.request.user)
        except LookupError:
            managed_cantons = []
        user_cantons_intersection = [
            orga.address_canton
            for orga in self.get_object().managed_organizations.all()
            if orga.address_canton in managed_cantons
        ]
        context["userprofilecanton"] = (
            user_cantons_intersection[0] if user_cantons_intersection else None
        )
        context["profile_is_coordinator"] = has_role(self.object, "coordinator")
        context["requester_is_state_manager"] = has_role(
            self.request.user, "state_manager"
        )
        context["user_has_a_role"] = self.get_object().groups.exists()
        context["return_url"] = get_return_url(self.request)
        return context


class UserUpdate(UserSelfAccessMixin, ProfileMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Profil mis à jour")

    def get_initial(self):
        """
        Pre-fill the form with the non-model fields
        """
        user = self.get_object()
        if hasattr(user, "profile"):
            struct = {}
            for field in self.profile_fields:
                struct[field] = getattr(user.profile, field)
            struct["actor_for"] = user.profile.actor_for.all()
            return struct

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["return_url"] = get_return_url(self.request)
        return context

    def get_success_url(self):
        return_url = get_return_url(self.request)
        if return_url:
            return return_url
        return super().get_success_url()

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
            return reverse_lazy("user-detail", kwargs={"pk": self.object.pk})
        except Exception:
            return reverse_lazy("user-list")


class UserProfileFilterSet(FilterSet):
    def __init__(self, data=None, *args, request=None, **kwargs):
        any_filter_is_set = bool(set(self.base_filters) & set(data or {}))
        if not any_filter_is_set:
            data = {}
            for name, f in self.base_filters.items():
                initial = f.extra.get("initial")
                # filter param is either missing or empty, use initial as default
                if not data.get(name) and initial:
                    data[name] = initial
        super().__init__(data=data, *args, request=request, **kwargs)

        if not has_permission(request.user, "user_export_all_fields"):
            # That user only has a limited amount of choices available, amend them
            # Remove the inaccessible statuses
            status_choices = self.filters["profile__status"].extra["choices"]
            self.filters["profile__status"].extra["choices"] = (
                t
                for t in status_choices
                if t[0]
                not in [
                    USERSTATUS_ARCHIVE,
                    USERSTATUS_DELETED,
                ]
            )
            # Remove filters that should be displayed to admins only
            del self.filters["roles"]
            del self.filters["profile__updated_at"]

    def filter_multi_nonempty(queryset, name, values):
        if values:
            allor_filter = [Q(**{name: v}) for v in values if v]
            if allor_filter:
                return queryset.filter(reduce(operator.or_, allor_filter))
        return queryset

    def filter_cantons(queryset, name, values):
        if values and any(values):
            # S'il y au moins un canton en commun
            allcantons_filter = [Q(profile__activity_cantons__overlap=values)] + [
                Q(profile__affiliation_canton=v) for v in values if v
            ]
            return queryset.filter(reduce(operator.or_, allcantons_filter))
        return queryset

    def filter_languages(queryset, name, values):
        if values and any(values):
            # S'il y au moins une langue en commun
            alllangs_filter = [Q(profile__languages_challenges__overlap=values)] + [
                Q(profile__language=v) for v in values if v
            ]
            return queryset.filter(reduce(operator.or_, alllangs_filter))
        return queryset

    def filter_wide(queryset, name, value):
        if value:
            allfields_filter = [
                Q(last_name__unaccent__icontains=value),
                Q(first_name__unaccent__icontains=value),
                Q(email__icontains=value),
                Q(profile__natel__icontains=value),
            ]
            return queryset.filter(reduce(operator.or_, allfields_filter))
        return queryset

    def filter_roles(queryset, name, value):
        try:
            # Use the '0' special value (see definition of the role filter) to specially filter the absence of any role
            if int(value[0]) == 0:
                return queryset.filter(groups__isnull=True)
        except (KeyError, ValueError):
            pass
        return queryset.filter(reduce(operator.or_, [Q(groups__name=r) for r in value]))

    def filter_updated_at(queryset, name, value):
        return queryset.filter(profile__updated_at__gte=value)

    profile__language = MultipleChoiceFilter(
        label=_("Langue"),
        choices=DV_LANGUAGES_WITH_DEFAULT,
        method=filter_multi_nonempty,
    )

    profile__languages_challenges = MultipleChoiceFilter(
        label=_("Langues d’animation"),
        choices=DV_LANGUAGES_WITH_DEFAULT,
        method=filter_languages,
    )

    profile__affiliation_canton = MultipleChoiceFilter(
        label=_("Canton d’affiliation"),
        choices=DV_STATE_CHOICES_WITH_DEFAULT,
        method=filter_multi_nonempty,
    )

    profile__activity_cantons = MultipleChoiceFilter(
        label=_("Cantons"), choices=DV_STATE_CHOICES_WITH_DEFAULT, method=filter_cantons
    )
    profile__status = MultipleChoiceFilter(
        label=_("Statut"),
        choices=USERSTATUS_CHOICES,
        initial=[
            USERSTATUS_ACTIVE,
            USERSTATUS_RESERVE,
        ],
    )
    profile__formation = MultipleChoiceFilter(
        label=_("Formation"), choices=FORMATION_CHOICES, method=filter_multi_nonempty
    )
    profile__actor_for = ModelMultipleChoiceFilter(
        label=_("Intervenant"),
        queryset=(
            QualificationActivity.objects.filter(category="C").prefetch_related(
                "translations"
            )
        ),
    )

    profile__updated_at = SwissDateFilter(
        label=_("Dernière modification après le"),
        method=filter_updated_at,
    )

    roles = MultipleChoiceFilter(
        label=_("Rôle"),
        choices=tuple((t[0] if t[0] else 0, t[1]) for t in DV_AVAILABLE_ROLES),
        method=filter_roles,
    )
    q = CharFilter(label=_("Recherche"), method=filter_wide)

    class Meta:
        model = get_user_model()
        fields = [
            "profile__status",
            "profile__formation",
            "profile__actor_for",
            "profile__activity_cantons",
            "profile__updated_at",
        ]


class UserList(HasPermissionsMixin, ProfileMixin, PaginatorMixin, FilterView):
    required_permission = "user_view_list"
    filterset_class = UserProfileFilterSet
    context_object_name = "users"


class UserListExport(ExportMixin, UserList):
    export_class = UserResource()
    export_filename = _("Utilisateurs")

    def get_export_class(self, request):
        """
        From ExportMixin
        Override export_class when User has no permission
        """
        if not has_permission(self.request.user, "user_export_all_fields"):
            return CollaboratorUserResource()
        return super().get_export_class(request)


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
            super(HelpersList, self)
            .get_queryset()
            .filter(profile__formation__in=FORMATION_KEYS)
        )


class ActorsList(UserDetailedList):
    page_title = _("Liste des intervenants")

    def get_queryset(self):
        return (
            super(ActorsList, self)
            .get_queryset()
            .exclude(profile__actor_for__isnull=True)
        )
