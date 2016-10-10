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
"""
Django settings for defivelo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import os

import dj_database_url

from . import get_env_variable
from .. import get_project_root_path

gettext = lambda s: s  # NOQA

PROJECT_ROOT = get_project_root_path()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_variable('SECRET_KEY', '')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(get_env_variable('DEBUG', False))

ALLOWED_HOSTS = tuple(get_env_variable('ALLOWED_HOSTS', '').splitlines())


# Application definition

UPSTREAM_APPS = (
    'bootstrap3',
    'bootstrap3_datetime',
    'django.contrib.sites',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'autocomplete_light',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'compressor',
    'stronghold',
    'localflavor',
    'parler',
    'multiselectfield',
    'django_filters',
    'import_export',
    'django_agpl',
    'tinymce',
    'taggit',
    'article',
    'rolepermissions',
)

# Project apps tested by jenkins (everything in apps/)
APPS_DIR = os.path.join(PROJECT_ROOT, 'apps')
EXCLUDED_DIRS = ('__pycache__')
PROJECT_APPS = tuple(['apps.' + aname
                     for aname in os.listdir(APPS_DIR)
                     if os.path.isdir(os.path.join(APPS_DIR, aname))
                     and aname not in EXCLUDED_DIRS])

INSTALLED_APPS = UPSTREAM_APPS + PROJECT_APPS + ('defivelo', )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'stronghold.middleware.LoginRequiredMiddleware',
)

ROOT_URLCONF = 'defivelo.urls'

WSGI_APPLICATION = 'defivelo.wsgi.application'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'defivelo/templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG
        },
    },
]

COMPRESS_PRECOMPILERS = (
    ('text/x-scss',
     os.path.join(
         get_env_variable('VIRTUAL_ENV',
                          os.path.join(PROJECT_ROOT, 'venv')
                          ),
         'bin', 'sassc') + ' {infile} {outfile}'),
)

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': dj_database_url.parse(get_env_variable('DATABASE_URL'))
}

SITE_ID = 1

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
# Internationalization
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Zurich'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DATE_FORMAT = 'j F Y'
DATE_FORMAT_SHORT = 'j.m'
TIME_FORMAT = 'G\hi'
TIME_FORMAT_SHORT = 'G:i'

LANGUAGES = (
    ('fr', gettext('French')),
    ('de', gettext('German')),
)

PARLER_LANGUAGES = {
    SITE_ID: (
        [{'code': lang[0]} for lang in LANGUAGES]
    ),
    'default': {
    }
}

# This allows you to put project-wide translations in the "locale" directory of
# your project
LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = get_env_variable('STATIC_URL', '/static/')

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# This is usually not used in a dev env, hence the default value
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = get_env_variable('STATIC_ROOT',
                               os.path.join(PROJECT_ROOT, 'static_files'))

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "defivelo/static"),
)

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = get_env_variable('MEDIA_URL', '/media/')

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = get_env_variable('MEDIA_ROOT', '/tmp/static/media')

# Adapt Stronghold for allauth
STRONGHOLD_PUBLIC_URLS = [r'^/admin/.*$', r'^/accounts/.*$']

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

TINYMCE_DEFAULT_CONFIG = {
    'theme': 'simple',
    'plugins': "autolink,",
    'cleanup_on_startup': True,
}


def defivelo_user_display(u):
    if u.first_name and u.last_name:
        return u'{first} {last}'.format(first=u.first_name, last=u.last_name)
    else:
        return u.email

ACCOUNT_USER_DISPLAY = defivelo_user_display
ACCOUNT_ADAPTER = 'defivelo.accounts.NoSignupAccountAdapter'

ROLEPERMISSIONS_MODULE = 'defivelo.roles'

# Email sender settings
SERVER_EMAIL = get_env_variable('SERVER_EMAIL', 'noreply@defi-velo.ch')
DEFAULT_FROM_EMAIL = \
    get_env_variable('DEFAULT_FROM_EMAIL', 'noreply@defi-velo.ch')

LOGIN_REDIRECT_URL = '/'


VCS_VERSION = get_env_variable('VCS_VERSION', '0')
VCS_COMMIT = get_env_variable('VCS_COMMIT', '0')

if VCS_VERSION == '0':
    import subprocess
    try:
        VCS_VERSION = subprocess.check_output(["git", "describe", "HEAD"])
        VCS_COMMIT = subprocess.check_output(["git", "rev-parse", "HEAD"])
    except (IOError, subprocess.CalledProcessError):
        VCS_VERSION = 'undefined'
        VCS_COMMIT = 'HEAD'

try:
    from django_agpl import app_settings as agpl_settings

    # Base directory from which download tree will be generated
    AGPL_ROOT = PROJECT_ROOT

    # Prefix of generated filename
    AGPL_FILENAME_PREFIX = 'defivelo-intranet'

    # Directories to exclude from download tree (optional)
    AGPL_EXCLUDE_DIRS = agpl_settings.EXCLUDE_DIRS + \
        [r'\.tox$',
         r'\.kdev4$',
         r'^__pycache__$',
         r'\.vagrant$', r'^virtualization',
         r'^static_files$', r'^venv$',
         r'^envdir$']

    # Files to exclude from download tree (optional)
    AGPL_EXCLUDE_FILES = agpl_settings.EXCLUDE_FILES + \
        [r'.mo$', r'~$', r'pgdump$', r'pg$', r'kdev4$']

    # Prefix to create inside download tree (optional)
    AGPL_TREE_PREFIX = 'defivelo-intranet'
except ImportError:
    pass  # Sorry
