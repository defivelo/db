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

from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms import Form as DjangoEmptyForm
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from rolepermissions.mixins import HasPermissionsMixin

from .mixins import ProfileMixin


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
    cantons = False

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
    cantons = False

    def dispatch(self, request, *args, **kwargs):
        # Forbid view if initial login hasn't been sent
        if self.get_object().profile.can_login and not self.initial_send:
            return (
                super(ResendUserCredentials, self)
                .dispatch(request, *args, **kwargs)
            )
        else:
            raise PermissionDenied