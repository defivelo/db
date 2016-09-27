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
from . import get_env_variable
from .base import *  # NOQA

DEBUG = bool(get_env_variable('DEBUG', True))
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG  # NOQA
SECRET_KEY = 'notsosecret'
NEVERCACHE_KEY = 'notsosecret'

INSTALLED_APPS += (  # NOQA
    'debug_toolbar',
    'django_extensions',
)

DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS": False}

INTERNAL_IPS = ('127.0.0.1',)
MIDDLEWARE_CLASSES += (  # NOQA
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

# Adapt Stronghold for Debug
STRONGHOLD_PUBLIC_URLS += [r'^/__debug__/.*$']  # NOQA

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
