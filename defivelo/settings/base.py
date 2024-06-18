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

from django.utils.translation import gettext_lazy as _

import dj_database_url
import dj_email_url

from .. import get_project_root_path
from . import get_env_variable


def gettext(s):
    return s


PROJECT_ROOT = get_project_root_path()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_variable("SECRET_KEY", "")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(get_env_variable("DEBUG", False))

ALLOWED_HOSTS = tuple(get_env_variable("ALLOWED_HOSTS", "").splitlines())

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

USE_X_FORWARDED_HOST = get_env_variable("USE_X_FORWARDED_HOST", False)

# Application definition

UPSTREAM_APPS = (
    "bootstrap3",
    "bootstrap3_datetime",
    "django.contrib.sites",
    "django.contrib.postgres",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap3",
    "compressor",
    "stronghold",
    "localflavor",
    "phonenumber_field",
    "parler",
    "django_countries",
    "django_filters",
    "import_export",
    "django_agpl",
    "tinymce",
    "taggit",
    "rolepermissions",
    "simple_history",
    "memoize",
)

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap3"
CRISPY_TEMPLATE_PACK = "bootstrap3"

# Project apps tested by jenkins (everything in apps/)
APPS_DIR = os.path.join(PROJECT_ROOT, "apps")
EXCLUDED_DIRS = "__pycache__"
PROJECT_APPS = tuple(
    [
        "apps." + aname
        for aname in os.listdir(APPS_DIR)
        if os.path.isdir(os.path.join(APPS_DIR, aname)) and aname not in EXCLUDED_DIRS
    ]
)

INSTALLED_APPS = PROJECT_APPS + UPSTREAM_APPS + ("defivelo",)

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "stronghold.middleware.LoginRequiredMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "defivelo.urls"

WSGI_APPLICATION = "defivelo.wsgi.application"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": True},
        "werkzeug": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
    },
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(PROJECT_ROOT, "defivelo/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "defivelo.context_processors.now",
            ],
            "debug": DEBUG,
        },
    },
]

SASSC_BIN_PATH = get_env_variable("SASSC_BIN_PATH", "/usr/bin/sassc")

COMPRESS_PRECOMPILERS = (
    (
        "text/x-scss",
        SASSC_BIN_PATH + " {infile} {outfile}",
    ),
)

COMPRESS_FILTERS = {
    "css": [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "compressor.filters.cssmin.CSSCompressorFilter",
    ],
    "js": ["compressor.filters.jsmin.JSMinFilter"],
}
# Only allow online compression because we are not able to pre-compress some dynamic assets
# (see declarations of "bootstrap3_extra_script" block in templates)
COMPRESS_OFFLINE = False
COMPRESS_ENABLED = True

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {"default": dj_database_url.parse(get_env_variable("DATABASE_URL"))}
# Allow using a password from a k8s secret
DATABASE_PASSWORD = get_env_variable("DATABASE_PASSWORD", False)
if DATABASE_PASSWORD:
    DATABASES["default"]["PASSWORD"] = DATABASE_PASSWORD


SITE_ID = 1

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
# Internationalization
LANGUAGE_CODE = "fr"
TIME_ZONE = "Europe/Zurich"
USE_I18N = True
USE_TZ = True

DATE_FORMAT = "j F Y"
DATE_FORMAT_SHORT = "j.m"
DATE_FORMAT_COMPACT = "j.m.y"
TIME_FORMAT = r"G\hi"
TIME_FORMAT_SHORT = "G:i"

LANGUAGES = (
    ("fr", gettext("French")),
    ("de", gettext("German")),
)

COUNTRIES_FIRST = [
    "CH",
]

PHONENUMBER_DEFAULT_REGION = "CH"

PARLER_LANGUAGES = {SITE_ID: ([{"code": lang[0]} for lang in LANGUAGES]), "default": {}}

# This allows you to put project-wide translations in the "locale" directory of
# your project
LOCALE_PATHS = (os.path.join(PROJECT_ROOT, "locale"),)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = get_env_variable("STATIC_URL", "/static/")

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# This is usually not used in a dev env, hence the default value
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = get_env_variable(
    "STATIC_ROOT", os.path.join(PROJECT_ROOT, "static_files")
)

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "defivelo/static"),
    os.path.join(PROJECT_ROOT, "ext/bootstrap-datetimepicker/build/"),
    os.path.join(PROJECT_ROOT, "ext/moment/min/"),
)

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = get_env_variable("MEDIA_URL", "/media/")

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = get_env_variable("MEDIA_ROOT", "/tmp/static/media")

# Adapt Stronghold for allauth
STRONGHOLD_PUBLIC_URLS = [
    r"^/admin/.*$",  # Administration
    r"^/accounts/.*$",  # Login
    r"^/agpl-.*$",  # License
]

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 500,
    "menubar": False,
    "plugins": ",".join(
        [
            "advlist",
            "autolink",
            "lists",
            "link",
            "image",
            "charmap",
            "print",
            "preview",
            "anchor",
            "searchreplace",
            "visualblocks",
            "code",
            "fullscreen",
            "insertdatetime",
            "media",
            "table",
            "paste",
            "code",
            "help",
            "wordcount",
        ]
    ),
    "toolbar": " | ".join(
        [
            " ".join(block)
            for block in [
                [
                    "formatselect",
                ],
                [
                    "bold",
                    "italic",
                    "underline",
                    "strikethrough",
                ],
                [
                    "undo",
                    "redo",
                ],
                [
                    "link",
                    "unlink",
                ],
                [
                    "alignleft",
                    "aligncenter",
                    "alignright",
                    "alignjustify",
                ],
                ["bullist", "numlist"],
                ["removeformat"],
            ]
        ]
    ),
    "branding": False,
}
TINYMCE_JS_URL = os.path.join(STATIC_URL, "tinymce/tinymce.min.js")
TINYMCE_JS_ROOT = os.path.join(STATIC_ROOT, "tinymce")
TINYMCE_INCLUDE_JQUERY = False
TINYMCE_COMPRESSOR = False


def defivelo_user_display(u):
    if u.first_name and u.last_name:
        return "{first} {last}".format(first=u.first_name, last=u.last_name)
    else:
        return u.email


ACCOUNT_USER_DISPLAY = defivelo_user_display
ACCOUNT_ADAPTER = "defivelo.accounts.NoSignupAccountAdapter"

SENTRY_DSN = get_env_variable("SENTRY_DSN", "")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=get_env_variable("SENTRY_ENVIRONMENT", ""),
    )


ROLEPERMISSIONS_MODULE = "defivelo.roles"

LOGIN_REDIRECT_URL = "/"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 2048  # Up from '1000'

VCS_VERSION = get_env_variable("VCS_VERSION", "0")
VCS_COMMIT = get_env_variable("VCS_COMMIT", "0")

if VCS_VERSION == "0":
    import subprocess

    try:
        VCS_VERSION = subprocess.check_output(
            ["git", "describe", "HEAD"], encoding="utf8"
        )
        VCS_COMMIT = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], encoding="utf8"
        )
    except (IOError, subprocess.CalledProcessError, UnicodeDecodeError):
        VCS_VERSION = "undefined"
        VCS_COMMIT = "HEAD"

try:
    from django_agpl import app_settings as agpl_settings

    # Base directory from which download tree will be generated
    AGPL_ROOT = PROJECT_ROOT

    # Prefix of generated filename
    AGPL_FILENAME_PREFIX = "defivelo-intranet"

    # Directories to exclude from download tree (optional)
    AGPL_EXCLUDE_DIRS = agpl_settings.EXCLUDE_DIRS + [
        r"\.tox$",
        r"\.kdev4$",
        r"^__pycache__$",
        r"\.vagrant$",
        r"^virtualization",
        r"^ext",
        r"^static_files$",
        r"^venv$",
        r"^envdir$",
    ]

    # Files to exclude from download tree (optional)
    AGPL_EXCLUDE_FILES = agpl_settings.EXCLUDE_FILES + [
        r".mo$",
        r"~$",
        r"pgdump$",
        r"pg$",
        r"kdev4$",
    ]

    # Prefix to create inside download tree (optional)
    AGPL_TREE_PREFIX = "defivelo-intranet"
except ImportError:
    pass  # Sorry


BOOTSTRAP3 = {
    "required_css_class": "required-field",
    "field_renderers": {
        "default": "defivelo.bootstrap3.DvFieldRenderer",
        "inline": "defivelo.bootstrap3.DvInlineFieldRenderer",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

#############
# E-Mailing #
#############
EMAIL_URL = get_env_variable("EMAIL_URL", "console://")
email_config = dj_email_url.parse(EMAIL_URL)

# Email sender settings
EMAIL_SUBJECT_PREFIX = _("DÉFI VÉLO: ")
SERVER_EMAIL = email_config.get(
    "SERVER_EMAIL", get_env_variable("SERVER_EMAIL", "noreply@defi-velo.ch")
)
DEFAULT_FROM_EMAIL = email_config.get(
    "DEFAULT_FROM_EMAIL", get_env_variable("DEFAULT_FROM_EMAIL", "noreply@defi-velo.ch")
)

# Email backend settings
EMAIL_FILE_PATH = email_config["EMAIL_FILE_PATH"]
EMAIL_HOST_USER = email_config["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = email_config["EMAIL_HOST_PASSWORD"]
EMAIL_HOST = email_config["EMAIL_HOST"]
EMAIL_PORT = email_config["EMAIL_PORT"]
EMAIL_BACKEND = email_config["EMAIL_BACKEND"]
EMAIL_USE_TLS = email_config["EMAIL_USE_TLS"]
EMAIL_USE_SSL = email_config["EMAIL_USE_SSL"]

WORK_PERMIT_CHOICES = [
    (0, "---"),
    (10, "Permis B UE/AELE"),
    (20, "Permis C UE/AELE"),
    (30, "Permis Ci UE/AELE"),
    (40, "Permis G UE/AELE"),
    (50, "Permis L UE/AELE"),
    (60, "Livret B Etat tiers"),
    (70, "Livret C Etat tiers"),
    (80, "Livret Ci Etat tiers"),
    (90, "Livret F Etat tiers"),
    (100, "Livret G Etat tiers"),
    (110, "Livret L Etat tiers"),
    (120, "Livret N Etat tiers"),
    (130, "Livret S Etat tiers"),
]

MARITAL_STATUS_CHOICES = [
    (0, "---------"),
    (10, "Célibataire"),
    (20, "Marié·e"),
    (30, "Divorcé·e"),
    (40, "Veu·f·ve"),
    (50, "En partenariat enregistré"),
    (60, "En partenariat dissous judiciairement"),
    (70, "En partenariat dissous par décès"),
    (80, "En partenariat dissous ensuite de déclaration d’absence"),
]
