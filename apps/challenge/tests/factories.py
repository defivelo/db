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
from factory import Faker, SubFactory, fuzzy
from factory.django import DjangoModelFactory

from apps.common import DV_SEASON_CHOICES, DV_SEASON_STATE_OPEN, DV_STATES
from apps.orga.tests.factories import OrganizationFactory
from apps.user.tests.factories import UserFactory

from ..models import (
    AnnualStateSetting,
    Invoice,
    InvoiceLine,
    Qualification,
    Season,
    Session,
)


class SeasonFactory(DjangoModelFactory):
    class Meta:
        model = Season

    year = fuzzy.FuzzyInteger(1999, 2050)
    season = fuzzy.FuzzyChoice([_s[0] for _s in DV_SEASON_CHOICES])
    # Juste un canton
    cantons = fuzzy.FuzzyChoice(DV_STATES)
    leader = factory.SubFactory(UserFactory)
    state = DV_SEASON_STATE_OPEN


class SessionFactory(DjangoModelFactory):
    class Meta:
        model = Session

    orga = factory.SubFactory(OrganizationFactory)
    day = fuzzy.FuzzyDate(date(1999, 1, 1), date(2050, 1, 1))


class QualificationFactory(DjangoModelFactory):
    class Meta:
        model = Qualification

    name = Faker("name")
    class_teacher_fullname = Faker("name")
    n_bikes = fuzzy.FuzzyInteger(1, 10)
    n_participants = fuzzy.FuzzyInteger(10, 20)


class AnnualStateSettingFactory(DjangoModelFactory):
    class Meta:
        model = AnnualStateSetting

    year = fuzzy.FuzzyInteger(1999, 2050)
    canton = fuzzy.FuzzyChoice(DV_STATES)


class InvoiceFactory(DjangoModelFactory):
    class Meta:
        model = Invoice

    season = SubFactory(SeasonFactory)
    organization = SubFactory(OrganizationFactory)
    ref = fuzzy.FuzzyText(length=20)
    status = fuzzy.FuzzyChoice([s[0] for s in Invoice.STATUS_CHOICES])


class InvoiceLineFactory(DjangoModelFactory):
    class Meta:
        model = InvoiceLine

    session = SubFactory(SessionFactory)
    invoice = SubFactory(InvoiceFactory)
    nb_bikes = fuzzy.FuzzyInteger(0, 20)
    nb_participants = fuzzy.FuzzyInteger(0, 20)
    cost_bikes = fuzzy.FuzzyDecimal(0, 400)
    cost_participants = fuzzy.FuzzyDecimal(0, 400)
