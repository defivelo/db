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

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from rolepermissions.checkers import has_role

from defivelo.roles import has_permission, user_cantons
from defivelo.views import MenuView

from ..forms import SimpleUserProfileForm, UserProfileForm
from ..models import (
    DV_PRIVATE_FIELDS,
    DV_PUBLIC_FIELDS,
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

    def get_form_class(self):
        try:
            user = self.object
        except AttributeError:
            user = self.get_object()
        if (
            not user
            or user.profile.affiliation_canton
            or UserProfileForm != self.form_class
        ):
            return self.form_class
        else:
            return SimpleUserProfileForm

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
        return qs.prefetch_related(
            "groups",
            "profile",
            "profile__actor_for",
            "profile__actor_for__translations",
        ).order_by("first_name", "last_name")

    def get_success_url(self):
        updatepk = self.get_object().pk
        if updatepk == self.request.user.pk:
            return reverse_lazy("profile-detail")
        return reverse_lazy("user-detail", kwargs={"pk": updatepk})

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        disabled_fields = []
        # if the edit user has access, extend the update_profile_fields
        if not has_permission(self.request.user, "user_crud_dv_public_fields"):
            disabled_fields += DV_PUBLIC_FIELDS
        if not has_permission(self.request.user, "user_crud_dv_private_fields"):
            disabled_fields += DV_PRIVATE_FIELDS
        if not has_permission(self.request.user, "user_edit_cresus_employee_number"):
            disabled_fields += ("cresus_employee_number",)
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
        if has_permission(self.request.user, "user_edit_cresus_employee_number"):
            update_profile_fields += ("cresus_employee_number",)

        (userprofile, created) = UserProfile.objects.get_or_create(user=user)
        for field in update_profile_fields:
            if field in form.cleaned_data:
                # For field updates that have date markers, note them properly
                if field in ["status", "bagstatus"]:
                    oldstatus = str(getattr(userprofile, field))
                    newstatus = form.cleaned_data[field]
                    if oldstatus != newstatus:
                        setattr(userprofile, "%s_updatetime" % field, timezone.now())
                modelfield = userprofile._meta.get_field(field)
                if modelfield.many_to_many or modelfield.one_to_many:
                    related_manager = getattr(userprofile, field)
                    related_manager.set(form.cleaned_data[field])
                else:
                    setattr(userprofile, field, form.cleaned_data[field])
        userprofile.save()
        return ret

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.get_form_class() == SimpleUserProfileForm and (
            self.request.user.is_superuser or has_role(self.request.user, "power_user")
        ):
            kwargs["affiliation_canton"] = True

        if self.cantons:
            try:
                kwargs["cantons"] = user_cantons(self.request.user)
            except LookupError:
                pass
        if self.form_class == UserProfileForm:
            # Ne permet qu'au bureau de créer des utilisateurs sans canton d'affiliation
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
            usercantons = []
        user = self.get_object()
        user_cantons_intersection = [
            orga.address_canton
            for orga in user.managed_organizations.all()
            if orga.address_canton in usercantons
        ]
        if (
            # Soit c'est moi
            request.user.pk == user.pk
            or
            # Soit j'ai le droit de lecture/écriture sur tous les cantons
            has_permission(request.user, "cantons_all")
            or
            # Soit j'ai le droit de lecture sur tous les cantons,
            # mais seulement le droit d'écriture sur mes cantons d'affiliation
            (
                has_permission(request.user, self.required_permission)
                and (
                    user_cantons_intersection
                    or
                    # Il est dans mes cantons d'affiliation
                    user.profile.affiliation_canton in usercantons
                    # Je ne fais que le consulter
                    or not edit
                )
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
