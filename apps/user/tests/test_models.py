# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015-2020 Didier Raboud <me+defivelo@odyx.org>
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

from rolepermissions.checkers import has_role

from apps.challenge.tests.factories import QualificationActivityFactory
from apps.user import FORMATION_M1, FORMATION_M2
from apps.user.tests.factories import UserFactory


def test_str_representations(db):
    user = UserFactory()

    assert str(user) == user.username
    assert str(user.profile) == user.get_full_name()


def test_automatic_collaborator_role_assignment_formation(db):
    user = UserFactory()
    user.profile.formation = FORMATION_M1
    user.profile.save()
    assert has_role(user, "collaborator")

    user.profile.formation = ""
    user.profile.save()
    assert not has_role(user, "collaborator")


def test_automatic_collaborator_role_assignment_actor(db):
    user = UserFactory()
    category_c = QualificationActivityFactory(category="C")
    category_c.save()
    user.profile.formation = ""
    user.profile.actor_for.add(category_c)
    user.profile.save()
    assert has_role(user, "collaborator")

    user.profile.actor_for.clear()
    user.profile.save()
    assert not has_role(user, "collaborator")


def test_automatic_collaborator_role_assignment_both(db):
    user = UserFactory()
    category_c = QualificationActivityFactory(category="C")
    category_c.save()
    user.profile.formation = FORMATION_M2
    user.profile.actor_for.add(category_c)
    user.profile.save()
    assert has_role(user, "collaborator")

    user.profile.actor_for.clear()
    user.profile.save()
    # Still has a formation
    assert has_role(user, "collaborator")

    user.profile.formation = ""
    user.profile.save()
    assert not has_role(user, "collaborator")
