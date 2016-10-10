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

from datetime import date

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from apps.common import DV_STATES
from apps.user.tests.factories import UserFactory
from apps.orga.tests.factories import OrganizationFactory

from ..models import Season, Session


class SeasonFactory(DjangoModelFactory):
    class Meta:
        model = Season

    begin = fuzzy.FuzzyDate(date(2015, 1, 1), date(2015, 5, 1))
    end = fuzzy.FuzzyDate(date(2015, 7, 1), date(2015, 12, 31))
    # Juste un canton
    cantons = fuzzy.FuzzyChoice(DV_STATES)
    leader = factory.SubFactory(UserFactory)

class SessionFactory(DjangoModelFactory):
    class Meta:
        model = Session

    organization = factory.SubFactory(OrganizationFactory)
    day = fuzzy.FuzzyDate(date(2015, 5, 2), date(2015, 6, 30))
