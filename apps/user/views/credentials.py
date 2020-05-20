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

from django.core.exceptions import PermissionDenied
from django.forms import Form as DjangoEmptyForm
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from rolepermissions.mixins import HasPermissionsMixin

from defivelo.roles import has_permission, user_cantons

from ..forms import UserAssignRoleForm
from .mixins import ProfileMixin


class UserCredentials(ProfileMixin, FormView):
    template_name = "auth/user_send_credentials.html"
    success_message = _("Données de connexion expédiées.")
    form_class = DjangoEmptyForm
    initial_send = True

    def dispatch(self, request, *args, **kwargs):
        self.managed_cantons = user_cantons(self.request.user)
        self.user_cantons_intersection = [
            orga.address_canton
            for orga in self.get_object().managed_organizations.all()
            if orga.address_canton in self.managed_cantons
        ]
        if (
            self.get_object().profile.affiliation_canton in self.managed_cantons
            or self.user_cantons_intersection
            # Useful when the edited user has no canton (affiliation_canton == '')
            or has_permission(self.request.user, "cantons_all")
        ):
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(UserCredentials, self).get_context_data(**kwargs)

        user_cantons_intersection = self.user_cantons_intersection + [
            self.get_object().profile.affiliation_canton
        ]
        context["userprofile"] = self.get_object()
        context["userprofilecanton"] = user_cantons_intersection
        context["initial_send"] = self.initial_send
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        context["fromuser"] = self.request.user
        user = self.get_object()
        user.profile.send_credentials(context, force=(not self.initial_send))
        return super(UserCredentials, self).form_valid(form)


class SendUserCredentials(HasPermissionsMixin, UserCredentials):
    required_permission = "user_can_send_credentials"
    cantons = False

    def dispatch(self, request, *args, **kwargs):
        # Forbid view if can already login
        if not self.get_object().profile.can_login:
            return super(SendUserCredentials, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied


class ResendUserCredentials(HasPermissionsMixin, UserCredentials):
    required_permission = "user_can_resend_credentials"
    success_message = _("Données de connexion ré-expédiées.")
    initial_send = False
    cantons = False

    def dispatch(self, request, *args, **kwargs):
        # Forbid view if initial login hasn't been sent
        if self.get_object().profile.can_login and not self.initial_send:
            return super(ResendUserCredentials, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied


class UserAssignRole(ProfileMixin, HasPermissionsMixin, FormView):
    template_name = "roles/assign.html"
    success_message = _("Rôle assigné à l'utilisa·teur·trice")
    form_class = UserAssignRoleForm
    required_permission = "user_set_role"
    cantons = False

    def dispatch(self, request, *args, **kwargs):
        # Forbid if self
        user = self.get_object()
        if user != self.request.user and user.profile.can_login:
            return super(UserAssignRole, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(UserAssignRole, self).get_context_data(**kwargs)
        context["userprofile"] = self.get_object()
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({"user": self.get_object()})
        return form_kwargs

    def form_valid(self, form):
        form.save()
        return super(UserAssignRole, self).form_valid(form)
