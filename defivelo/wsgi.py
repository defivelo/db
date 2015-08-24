"""
WSGI config for defivelo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os

from defivelo import get_project_root_path, import_env_vars

import_env_vars(os.path.join(get_project_root_path(), 'envdir', 'local'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "defivelo.settings.base")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
