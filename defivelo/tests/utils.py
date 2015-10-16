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
from __future__ import unicode_literals

from allauth.account.models import EmailAddress, EmailConfirmation
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone
from django.utils.translation import activate


class AuthClient(Client):
    USERNAME = 'foobar-authenticated'
    PASSWORD = 'sicrit'
    EMAIL = 'test@example.com'

    def __init__(self):
        super(AuthClient, self).__init__()
        # Create that user
        self.user = get_user_model().objects.create_user(
            username=self.USERNAME, password=self.PASSWORD,
            email=self.EMAIL
        )
        # Create his trusted Email
        EmailAddress.objects.create(user=self.user, email=self.EMAIL,
                                    verified=True, primary=True)
        self.login(email=self.EMAIL, password=self.PASSWORD)

        self.language = 'fr'
        activate(self.language)
