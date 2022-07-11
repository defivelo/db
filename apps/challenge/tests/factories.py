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

from datetime import date

from django.utils.dates import MONTHS

import factory
from factory import Faker, SubFactory, fuzzy
from factory.django import DjangoModelFactory

from apps.common import DV_SEASON_STATE_OPEN, DV_STATES
from apps.orga.tests.factories import OrganizationFactory
from apps.user.tests.factories import UserFactory

from .. import CHOSEN_AS_ACTOR, CHOSEN_AS_HELPER, CHOSEN_AS_LEADER
from ..models import (
    AnnualStateSetting,
    HelperSessionAvailability,
    Invoice,
    InvoiceLine,
    Qualification,
    QualificationActivity,
    Season,
    Session,
)
from ..models.qualification import CATEGORY_CHOICES
from ..models.registration import Registration


class SeasonFactory(DjangoModelFactory):
    class Meta:
        model = Season

    year = fuzzy.FuzzyInteger(1999, 2050)
    month_start = fuzzy.FuzzyChoice([k for k, v in MONTHS.items()])
    n_months = fuzzy.FuzzyInteger(1, 15)
    # Juste un canton
    cantons = [fuzzy.FuzzyChoice(DV_STATES).fuzz()]
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

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        If actor and session is provided, make sure an actor availability object
        exists for this session.
        """
        if "actor" in kwargs and "session" in kwargs:
            HelperSessionAvailability.objects.get_or_create(
                session=kwargs["session"],
                helper=kwargs["actor"],
                availability="y",
                chosen_as=CHOSEN_AS_ACTOR,
            )

        if "leader" in kwargs and "session" in kwargs:
            HelperSessionAvailability.objects.get_or_create(
                session=kwargs["session"],
                helper=kwargs["leader"],
                availability="y",
                chosen_as=CHOSEN_AS_LEADER,
            )
        return super()._create(model_class, *args, **kwargs)

    @factory.post_generation
    def helpers(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for helper in extracted:
                HelperSessionAvailability.objects.get_or_create(
                    session=self.session,
                    helper=helper,
                    availability="y",
                    chosen_as=CHOSEN_AS_HELPER,
                )
                self.helpers.add(helper)


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


class QualificationActivityFactory(DjangoModelFactory):
    class Meta:
        model = QualificationActivity

    name = Faker("name")
    category = fuzzy.FuzzyChoice([c[0] for c in CATEGORY_CHOICES])


class RegistrationFactory(DjangoModelFactory):
    class Meta:
        model = Registration
