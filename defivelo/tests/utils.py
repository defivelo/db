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

from django.contrib.auth import get_user_model
from django.test import Client
from django.utils.translation import activate

from allauth.account.models import EmailAddress
from faker import Faker
from rolepermissions.checkers import has_role
from rolepermissions.roles import assign_role

from apps.common import DV_STATES
from apps.user import FORMATION_M1, get_new_username
from apps.user.models import UserManagedState, UserProfile

fake = Faker()


class AuthClient(Client):
    role = None

    def __init__(self):
        super(AuthClient, self).__init__()
        self.USERNAME = get_new_username()
        self.PASSWORD = fake.password()
        self.EMAIL = fake.email()

        # Create that user
        self.user = get_user_model().objects.create_user(
            username=self.USERNAME,
            password=self.PASSWORD,
            email=self.EMAIL,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )
        UserProfile.objects.get_or_create(user=self.user)
        # Create his trusted Email
        EmailAddress.objects.create(
            user=self.user, email=self.EMAIL, verified=True, primary=True
        )
        self.login(email=self.EMAIL, password=self.PASSWORD)

        self.language = "fr"
        activate(self.language)

        if self.role:
            assign_role(self.user, self.role)


class CollaboratorAuthClient(AuthClient):
    def __init__(self):
        super().__init__()
        self.user.profile.formation = FORMATION_M1
        self.user.profile.save()
        assert has_role(self.user, "collaborator")


class StateManagerAuthClient(AuthClient):
    role = "state_manager"

    def __init__(self):
        super(StateManagerAuthClient, self).__init__()
        # Make hir manager for one state
        UserManagedState.objects.get_or_create(user=self.user, canton=DV_STATES[0])


class PowerUserAuthClient(AuthClient):
    role = "power_user"


class CoordinatorAuthClient(AuthClient):
    role = "coordinator"


class SuperUserAuthClient(AuthClient):
    def __init__(self):
        super(SuperUserAuthClient, self).__init__()
        self.user.is_superuser = True
        self.user.save()
