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
from django.core.urlresolvers import reverse
from django.forms import Form as DjangoEmptyForm
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from rolepermissions.mixins import HasPermissionsMixin

from .mixins import ProfileMixin


class UserDelete(ProfileMixin, HasPermissionsMixin, FormView):
    template_name = "delete/user_delete.html"
    success_message = _("Utilisateur supprimé")
    form_class = DjangoEmptyForm
    required_permission = "user_deletions"
    cantons = False

    def get_context_data(self, **kwargs):
        context = super(UserDelete, self).get_context_data(**kwargs)
        # Add our menu_category context
        context["userprofile"] = self.get_object()
        context["current_site"] = Site.objects.get_current()
        context["login_uri"] = self.request.build_absolute_uri(reverse("account_login"))
        return context

    def form_valid(self, form):
        user = self.get_object()
        user.profile.delete()
        return super(UserDelete, self).form_valid(form)
