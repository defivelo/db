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
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.utils import timezone

from defivelo.roles import has_permission, user_cantons
from defivelo.views import MenuView

from ..forms import UserProfileForm
from ..models import (
    DV_PRIVATE_FIELDS,
    DV_PUBLIC_FIELDS,
    MULTISELECTFIELD_REGEXP,
    PERSONAL_FIELDS,
    STD_PROFILE_FIELDS,
    UserProfile,
)


class ProfileMixin(MenuView):
    cantons = True
    model = get_user_model()
    context_object_name = "userprofile"
    form_class = UserProfileForm
    profile_fields = STD_PROFILE_FIELDS

    def get_context_data(self, **kwargs):
        context = super(ProfileMixin, self).get_context_data(**kwargs)
        context["current_site"] = Site.objects.get_current()
        # Add our menu_category context
        context["menu_category"] = "user"
        context["login_uri"] = self.request.build_absolute_uri(reverse("account_login"))
        return context

    def get_object(self):
        """
        Fallback to myself when accessing the profile
        """
        resolvermatch = self.request.resolver_match
        return self.model.objects.get(
            pk=int(resolvermatch.kwargs.get("pk", self.request.user.pk))
        )

    def get_queryset(self):
        try:
            qs = super(ProfileMixin, self).get_queryset()
        except AttributeError:
            qs = get_user_model().objects

        qs = qs.prefetch_related(
            "groups",
            "profile",
            "profile__actor_for",
            "profile__actor_for__translations",
        ).order_by("first_name", "last_name")
        try:
            usercantons = user_cantons(self.request.user)
        except LookupError:
            raise PermissionDenied
        if usercantons:
            # S'il y au moins un canton en commun
            cantons_regexp = MULTISELECTFIELD_REGEXP % "|".join(
                [v for v in usercantons if v]
            )
            allcantons_filter = [Q(profile__activity_cantons__regex=cantons_regexp)] + [
                Q(profile__affiliation_canton__in=usercantons)
            ]
            qs = qs.filter(reduce(operator.or_, allcantons_filter))
        return qs

    def get_success_url(self):
        updatepk = self.get_object().pk
        if updatepk == self.request.user.pk:
            return reverse_lazy("profile-detail")
        return reverse_lazy("user-detail", kwargs={"pk": updatepk})

    def get_form(self, *args, **kwargs):
        form = super(ProfileMixin, self).get_form(*args, **kwargs)
        disabled_fields = []
        # if the edit user has access, extend the update_profile_fields
        if not has_permission(self.request.user, "user_crud_dv_public_fields"):
            disabled_fields += DV_PUBLIC_FIELDS
        if not has_permission(self.request.user, "user_crud_dv_private_fields"):
            disabled_fields += DV_PRIVATE_FIELDS
        for field in form.fields:
            if field in disabled_fields:
                form.fields[field].disabled = True
        return form

    def form_valid(self, form):
        ret = super(ProfileMixin, self).form_valid(form)
        """
        Write the non-model fields
        """
        try:
            user = self.object
        except AttributeError:
            user = self.get_object()

        update_profile_fields = PERSONAL_FIELDS
        # if the edit user has access, extend the update_profile_fields
        if has_permission(self.request.user, "user_crud_dv_public_fields"):
            update_profile_fields += DV_PUBLIC_FIELDS
        if has_permission(self.request.user, "user_crud_dv_private_fields"):
            update_profile_fields += DV_PRIVATE_FIELDS

        (userprofile, created) = UserProfile.objects.get_or_create(user=user)
        for field in update_profile_fields:
            if field in form.cleaned_data:
                # For field updates that have date markers, note them properly
                if field in ["status", "bagstatus"]:
                    oldstatus = str(getattr(userprofile, field))
                    newstatus = form.cleaned_data[field]
                    if oldstatus != newstatus:
                        setattr(userprofile, "%s_updatetime" % field, timezone.now())
                setattr(userprofile, field, form.cleaned_data[field])
        userprofile.save()
        return ret

    def get_form_kwargs(self):
        kwargs = super(ProfileMixin, self).get_form_kwargs()
        if self.cantons:
            try:
                kwargs["cantons"] = user_cantons(self.request.user)
            except LookupError:
                pass
        if self.form_class == UserProfileForm:
            kwargs["affiliation_canton_required"] = not has_permission(
                self.request.user, "cantons_all"
            )
        return kwargs


class UserSelfAccessMixin(object):
    required_permission = "user_edit_other"

    def dispatch(self, request, *args, **kwargs):
        edit = kwargs.pop("edit", False)
        try:
            usercantons = user_cantons(request.user)
        except LookupError:
            usercantons = False

        user = self.get_object()
        if (
            # Soit c'est moi
            request.user.pk == user.pk
            or
            # Soit j'ai le droit sur tous les cantons
            has_permission(request.user, "cantons_all")
            or
            # Soit il est dans mes cantons et j'ai droit
            (
                usercantons
                and (
                    # Il est dans mes cantons d'affiliation
                    user.profile.affiliation_canton in usercantons
                    or (
                        # Je ne fais que le consulter et il est dans mes
                        # cantons d'activité
                        not edit
                        and user.profile.activity_cantons
                        and len(
                            set(user.profile.activity_cantons).intersection(usercantons)
                        )
                        != 0
                    )
                )
                and has_permission(request.user, self.required_permission)
            )
        ):
            return super(UserSelfAccessMixin, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_form_kwargs(self):
        kwargs = super(UserSelfAccessMixin, self).get_form_kwargs()
        if has_permission(self.request.user, self.required_permission):
            kwargs["allow_email"] = True
        try:
            kwargs["cantons"] = user_cantons(self.request.user)
        except LookupError:
            pass
        return kwargs
