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
from . import get_env_variable
from .base import *  # noqa

DEBUG = bool(get_env_variable('DEBUG', True))
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
SECRET_KEY = 'notsosecret'
NEVERCACHE_KEY = 'notsosecret'

INSTALLED_APPS += (
    'django_jenkins',
)

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.with_coverage',
    # 'django_jenkins.tasks.run_jshint',
    # 'django_jenkins.tasks.run_csslint',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes',
    'django_jenkins.tasks.run_flake8',
    # 'django_jenkins.tasks.run_sloccount',
    # 'django_jenkins.tasks.run_graphmodels',
)
