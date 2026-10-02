from django.contrib.auth import get_user_model

import pytest

from apps.challenge import (
    CHOICE_CHOICES,
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_LEGACY,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
)
from apps.challenge.fields import (
    ActorChoiceField,
    BSAvailabilityRadioSelect,
    BSChoiceRadioSelect,
    HelpersChoiceField,
    LeaderChoiceField,
)
from apps.challenge.models import HelperSessionAvailability
from apps.user import FORMATION_M2
from apps.user.tests.factories import UserFactory

from .factories import QualificationActivityFactory, SessionFactory

User = get_user_model()


def options_by_value(widget):
    context = widget.get_context("choice", None, {})
    return {
        opts[0]["value"]: opts[0] for _, opts, _ in context["widget"]["optgroups"]
    }, context


def test_choice_radio_select_decorates_each_option():
    widget = BSChoiceRadioSelect(choices=CHOICE_CHOICES, user_assignment=None)
    options, context = options_by_value(widget)

    assert context["widget"]["forbid_absence"] is None
    assert options[CHOSEN_AS_LEADER]["text"] == "M2"
    assert options[CHOSEN_AS_LEADER]["class"] == "success"
    assert options[CHOSEN_AS_HELPER]["text"] == "M1"
    assert options[CHOSEN_AS_HELPER]["class"] == "success"
    assert options[CHOSEN_AS_REPLACEMENT]["text"] == "S"
    assert options[CHOSEN_AS_REPLACEMENT]["class"] == "warning"
    assert options[CHOSEN_AS_ACTOR]["glyphicon"] == "sunglasses"
    assert options[CHOSEN_AS_ACTOR]["class"] == "success"
    assert options[CHOSEN_AS_LEGACY]["glyphicon"] == "ok-sign"
    assert options[CHOSEN_AS_LEGACY]["class"] == "warning"
    assert options[CHOSEN_AS_NOT]["glyphicon"] == "remove-circle"
    assert options[CHOSEN_AS_NOT]["class"] == "default"
    assert options[CHOSEN_AS_LEADER]["glyphicon"] is None


def test_choice_radio_select_enabled_without_assignment():
    widget = BSChoiceRadioSelect(choices=CHOICE_CHOICES, user_assignment=None)
    options, _ = options_by_value(widget)
    assert not any(o["disabled"] for o in options.values())


def test_choice_radio_select_disabled_with_assignment():
    widget = BSChoiceRadioSelect(
        choices=CHOICE_CHOICES, user_assignment=CHOSEN_AS_HELPER
    )
    options, _ = options_by_value(widget)
    assert all(o["disabled"] for o in options.values())


def test_choice_radio_select_default_assignment_disables_all():
    widget = BSChoiceRadioSelect(choices=CHOICE_CHOICES)
    options, _ = options_by_value(widget)
    assert all(o["disabled"] for o in options.values())


@pytest.mark.parametrize("forbid_absence", [True, False])
def test_availability_radio_select_forwards_forbid_absence(forbid_absence):
    widget = BSAvailabilityRadioSelect(
        choices=HelperSessionAvailability.AVAILABILITY_CHOICES,
        forbid_absence=forbid_absence,
    )
    context = widget.get_context("availability", "y", {})
    assert context["widget"]["forbid_absence"] is forbid_absence


@pytest.fixture
def session(db):
    return SessionFactory()


@pytest.fixture
def helper(db):
    return UserFactory(first_name="Jane", last_name="Doe")


def choose(session, helper, chosen_as):
    HelperSessionAvailability.objects.create(
        session=session, helper=helper, availability="y", chosen_as=chosen_as
    )


def test_get_chosen_as_without_session(helper):
    field = LeaderChoiceField(queryset=User.objects.all())
    assert field.get_chosen_as(helper) is None


def test_get_chosen_as_without_availability(session, helper):
    field = LeaderChoiceField(queryset=User.objects.all(), session=session)
    assert field.get_chosen_as(helper) is None
    assert field.if_replacement(helper) == ""


def test_leader_label_marks_replacement(session, helper):
    choose(session, helper, CHOSEN_AS_REPLACEMENT)
    field = LeaderChoiceField(queryset=User.objects.all(), session=session)
    assert field.label_from_instance(helper) == "Jane Doe (S)"


def test_leader_label_without_replacement(session, helper):
    choose(session, helper, CHOSEN_AS_LEADER)
    field = LeaderChoiceField(queryset=User.objects.all(), session=session)
    assert field.label_from_instance(helper) == "Jane Doe"


def test_helpers_label_hides_m1_formation(session, helper):
    field = HelpersChoiceField(queryset=User.objects.all(), session=session)
    assert field.label_from_instance(helper) == "Jane Doe"


def test_helpers_label_shows_m2_formation_and_replacement(session, helper):
    helper.profile.formation = FORMATION_M2
    helper.profile.save()
    choose(session, helper, CHOSEN_AS_REPLACEMENT)
    field = HelpersChoiceField(queryset=User.objects.all(), session=session)
    assert field.label_from_instance(helper) == "Jane Doe (M2) (S)"


def test_actor_label_lists_activities(session, helper):
    activity = QualificationActivityFactory(name="Rencontre police", category="C")
    helper.profile.actor_for.add(activity)
    field = ActorChoiceField(queryset=User.objects.all(), session=session)
    assert field.label_from_instance(helper) == "Jane Doe (Rencontre police)"
