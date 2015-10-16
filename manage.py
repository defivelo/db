#!/usr/bin/env python
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
import os
import sys

from defivelo import get_project_root_path, import_env_vars

if __name__ == "__main__":
    if 'test' in sys.argv:
        env_dir = os.path.join('envdir', 'tests')
    else:
        env_dir = os.path.join('envdir', 'local')

    import_env_vars(os.path.join(get_project_root_path(), env_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "defivelo.settings.dev")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
