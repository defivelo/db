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

from factory import Faker
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from apps.common import DV_STATES

from ..models import Organization


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    name = Faker("name")
    address_street = Faker("street_name")
    address_no = Faker("random_int", min=0, max=999)
    address_zip = Faker("random_int", min=1000, max=9999)
    address_city = Faker("city")
    address_canton = FuzzyChoice(DV_STATES)
