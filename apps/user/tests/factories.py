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

from django.contrib.auth import get_user_model

import factory
from factory import Faker
from factory.django import DjangoModelFactory

from apps.user import FORMATION_M1
from apps.user.models import USERSTATUS_ACTIVE, UserProfile, get_new_username


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    formation = FORMATION_M1
    status = USERSTATUS_ACTIVE


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    profile = factory.RelatedFactory(UserProfileFactory, "user")
    username = factory.LazyFunction(get_new_username)
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    email = factory.Sequence(lambda n: "user%d@example.com" % n)
    # Normal users can't login, and don't have passwords
    password = factory.PostGenerationMethodCall("set_unusable_password")
    is_active = False
