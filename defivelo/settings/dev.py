from . import get_env_variable
from .base import *  # noqa

DEBUG = bool(get_env_variable('DEBUG', True))
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
SECRET_KEY = 'notsosecret'
NEVERCACHE_KEY = 'notsosecret'

INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
)

DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS": False}

INTERNAL_IPS = ('127.0.0.1',)
MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

# Adapt Stronghold for Debug
STRONGHOLD_PUBLIC_URLS += [r'^/__debug__/.*$']
