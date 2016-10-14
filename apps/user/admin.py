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
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import UserManagedState, UserProfile

admin.site.register(UserProfile)
admin.site.register(UserManagedState)

# Monkey-patch the get_username, mostly for the admin


def get_user_model_safe():
    """
    Get the user model before it is loaded, but after the app registry
    is populated
    """
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    app_config = apps.get_app_config(app_label)
    models_module = import_module("%s.%s" % (app_config.name, "models"))
    return getattr(models_module, model_name)


def username(self):
    return _('{fullname} <{email}>').format(
        fullname=self.get_full_name(),
        email=self.email)

get_user_model_safe().get_username = username
