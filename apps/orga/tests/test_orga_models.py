from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

import pytest

from apps.orga.models import (
    ORGASTATUS_ACTIVE,
    ORGASTATUS_INACTIVE,
    ORGASTATUS_UNDEF,
    Organization,
)
from apps.orga.tests.factories import OrganizationFactory
from apps.user.models import UserManagedState
from apps.user.tests.factories import UserFactory


def _orga(**kwargs):
    defaults = {"name": "École du Lac", "abbr": "EDL", "address_city": "Nyon"}
    defaults.update(kwargs)
    return Organization(**defaults)


def test_abbr_or_name_prefers_abbr():
    assert _orga().abbr_or_name == "EDL"


def test_abbr_or_name_falls_back_to_stripped_name():
    assert _orga(abbr="", name="  École  ").abbr_or_name == "École"


def test_ifabbr_with_abbr_is_abbr_tag():
    assert _orga().ifabbr == '<abbr title="École du Lac">EDL</abbr>'


def test_ifabbr_without_abbr_is_name():
    assert _orga(abbr="").ifabbr == "École du Lac"


@pytest.mark.parametrize(
    "status,icon,css_class",
    [
        (ORGASTATUS_ACTIVE, "star", "success"),
        (ORGASTATUS_INACTIVE, "hourglass", "danger"),
    ],
)
def test_status_icon_and_class(status, icon, css_class):
    orga = _orga(status=status)
    assert f"glyphicon-{icon}" in orga.status_icon()
    assert f'title="{orga.status_full}"' in orga.status_icon()
    assert orga.status_class() == css_class


def test_undefined_status():
    orga = _orga(status=ORGASTATUS_UNDEF)
    assert orga.status_full == ""
    assert orga.status_icon() == ""
    assert orga.status_class() == "default"


def test_status_full_label():
    assert str(_orga(status=ORGASTATUS_ACTIVE).status_full) == "Actif"


def test_shortname_and_str_with_city():
    orga = _orga()
    assert orga.shortname() == '<abbr title="École du Lac">EDL</abbr> (Nyon)'
    assert str(orga) == "École du Lac (Nyon)"


def test_shortname_and_str_without_city():
    orga = _orga(abbr="", address_city="")
    assert orga.shortname() == "École du Lac"
    assert str(orga) == "École du Lac"


def test_address_canton_full():
    assert _orga(address_canton="VD").address_canton_full == "Vaud"


@pytest.mark.django_db
def test_get_absolute_url():
    orga = OrganizationFactory()
    assert orga.get_absolute_url().endswith(f"/orga/{orga.pk}/")


@pytest.mark.django_db
def test_get_state_managers_returns_users_managing_canton():
    vd_manager = UserFactory()
    ge_manager = UserFactory()
    UserManagedState.objects.create(user=vd_manager, canton="VD")
    UserManagedState.objects.create(user=ge_manager, canton="GE")
    orga = OrganizationFactory(address_canton="VD")
    assert list(orga.get_state_managers()) == [vd_manager]


@pytest.fixture
def message_request():
    request = RequestFactory().get("/")
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


@pytest.mark.django_db
def test_notify_new_registrations_mails_state_managers(message_request, mailoutbox):
    manager = UserFactory(email="manager@example.com")
    other = UserFactory(email="other@example.com")
    UserManagedState.objects.create(user=manager, canton="VD")
    UserManagedState.objects.create(user=other, canton="GE")
    orga = OrganizationFactory(address_canton="VD")

    orga.notify_new_registrations(message_request)

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert "manager@example.com" in mail.to[0]
    assert "Nouvelles pré-inscriptions à valider" in mail.subject
    assert "http://testserver" in mail.body
    stored = [str(m) for m in get_messages(message_request)]
    assert len(stored) == 1
    assert "préinscription a été enregistrée" in stored[0]


@pytest.mark.django_db
def test_notify_registrations_validated_mails_coordinator(message_request, mailoutbox):
    coordinator = UserFactory(email="coord@example.com")
    orga = OrganizationFactory(coordinator=coordinator, address_city="Nyon")

    orga.notify_registrations_validated(message_request)

    assert len(mailoutbox) == 1
    assert "coord@example.com" in mailoutbox[0].to[0]
    assert "Vos inscriptions à DEFIVELO" in mailoutbox[0].subject
    stored = [str(m) for m in get_messages(message_request)]
    assert stored == [
        f"L'inscription pour l'établissement {orga} est enregistrée, et un "
        "email a été envoyé à la personne coordinatrice."
    ]
