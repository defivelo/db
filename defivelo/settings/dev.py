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
from . import get_env_variable
from .base import *

DEBUG = bool(get_env_variable("DEBUG", True))
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG
SECRET_KEY = "notsosecret"
NEVERCACHE_KEY = "notsosecret"

COMPRESS_ENABLED = False

INSTALLED_APPS += (
    "debug_toolbar",
    "django_extensions",
)


def show_toolbar(request):
    from django.conf import settings

    return settings.DEBUG


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar,
    "INTERCEPT_REDIRECTS": False,
}

INTERNAL_IPS = (
    "127.0.0.1",
    "10.0.3.1",
)
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Adapt Stronghold for Debug
STRONGHOLD_PUBLIC_URLS += [r"^/__debug__/.*$"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
