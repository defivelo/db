import pytest

from apps.challenge import (
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_LEGACY,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
)
from apps.challenge.models import HelperSessionAvailability
from apps.challenge.models.availability import HelperSeasonWorkWish
from apps.user.tests.factories import UserFactory

from .factories import SeasonFactory, SessionFactory


def make_availability(chosen_as=CHOSEN_AS_NOT, availability="y"):
    return HelperSessionAvailability(
        session=SessionFactory.build(),
        helper=UserFactory.build(first_name="Jane", last_name="Doe"),
        availability=availability,
        chosen_as=chosen_as,
    )


@pytest.mark.parametrize(
    "chosen_as,expected",
    [
        (CHOSEN_AS_NOT, False),
        (CHOSEN_AS_LEGACY, True),
        (CHOSEN_AS_HELPER, True),
        (CHOSEN_AS_REPLACEMENT, True),
    ],
)
def test_chosen(chosen_as, expected):
    assert make_availability(chosen_as).chosen is expected


@pytest.mark.parametrize(
    "chosen_as,expected",
    [
        (CHOSEN_AS_HELPER, "M1"),
        (CHOSEN_AS_LEADER, "M2"),
        (CHOSEN_AS_REPLACEMENT, "S"),
        (CHOSEN_AS_LEGACY, ""),
        (CHOSEN_AS_NOT, ""),
    ],
)
def test_chosen_as_icon_text(chosen_as, expected):
    assert str(make_availability(chosen_as).chosen_as_icon) == expected


def test_chosen_as_icon_actor_is_glyphicon():
    icon = make_availability(CHOSEN_AS_ACTOR).chosen_as_icon
    assert "glyphicon-sunglasses" in icon
    assert "Intervenant·e" in icon


@pytest.mark.parametrize(
    "chosen_as,expected",
    [
        (CHOSEN_AS_HELPER, "Moniteur·trice 1"),
        (CHOSEN_AS_LEADER, "Moniteur·trice 2"),
        (CHOSEN_AS_REPLACEMENT, "Moniteur·trice de secours"),
        (CHOSEN_AS_ACTOR, "Intervenant·e"),
        (CHOSEN_AS_LEGACY, "Choisi"),
        (CHOSEN_AS_NOT, ""),
    ],
)
def test_chosen_as_verb(chosen_as, expected):
    assert str(make_availability(chosen_as).chosen_as_verb) == expected


@pytest.mark.parametrize(
    "availability,icon,title",
    [
        ("y", "ok-sign", "Oui"),
        ("i", "ok-circle", "Si nécessaire"),
        ("n", "remove-sign", "Non"),
    ],
)
def test_availability_icon(availability, icon, title):
    html = make_availability(availability=availability).availability_icon
    assert f"glyphicon-{icon}" in html
    assert title in html


@pytest.mark.parametrize(
    "availability,expected",
    [
        ("y", "Jane Doe est disponible"),
        ("i", "Jane Doe est disponible si nécessaire"),
        ("n", "Jane Doe n'est pas disponible"),
    ],
)
def test_str_availability(availability, expected):
    assert str(make_availability(availability=availability)).endswith(expected)


def test_str_includes_chosen_as_when_chosen():
    text = str(make_availability(chosen_as=CHOSEN_AS_LEADER))
    assert f"({CHOSEN_AS_LEADER}) Jane Doe" in text


def test_str_omits_chosen_as_when_not_chosen():
    text = str(make_availability(chosen_as=CHOSEN_AS_NOT))
    assert "(" not in text.split(":")[-1]


def test_work_wish_str():
    season = SeasonFactory.build()
    wish = HelperSeasonWorkWish(
        season=season,
        helper=UserFactory.build(first_name="Jane", last_name="Doe"),
        amount=3,
    )
    assert str(wish) == f"{season}: Jane Doe aimerait travailler 3 fois"
