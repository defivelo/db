# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016 Didier Raboud <me+defivelo@odyx.org>
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

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from apps.user.models import UserProfile


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    profile = factory.RelatedFactory(UserProfileFactory, 'user')
    username = factory.Sequence(lambda n: "user%d" % n)
    email = factory.Sequence(lambda n: "user%d@example.com" % n)
    # Normal users can't login, and don't have passwords
    password = factory.PostGenerationMethodCall('set_unusable_password')
    is_active = False
