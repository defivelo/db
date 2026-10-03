import datetime

from django.contrib import admin
from django.urls import reverse

import pytest

from apps.challenge.admin import QualificationActivityAdmin, SessionAdmin
from apps.challenge.models import QualificationActivity, Session
from apps.orga.tests.factories import OrganizationFactory
from defivelo.tests.utils import (
    CollaboratorAuthClient,
    CoordinatorAuthClient,
    StateManagerAuthClient,
)

from .factories import (
    QualificationActivityFactory,
    QualificationFactory,
    RegistrationFactory,
    SessionFactory,
)

DAY = datetime.date(2030, 3, 4)


@pytest.fixture
def session(db):
    return SessionFactory(orga__address_canton="VD", day=DAY)


def test_quali_create_forbidden_without_session_crud(season, session):
    url = reverse(
        "quali-create", kwargs={"seasonpk": season.pk, "sessionpk": session.pk}
    )
    assert CollaboratorAuthClient().get(url).status_code == 403


def test_quali_delete_forbidden_without_session_crud(season, session):
    quali = QualificationFactory(session=session)
    url = reverse(
        "quali-delete",
        kwargs={"seasonpk": season.pk, "sessionpk": session.pk, "pk": quali.pk},
    )
    assert CollaboratorAuthClient().get(url).status_code == 403


@pytest.mark.parametrize("url_name", ["registration-create", "registration-confirm"])
def test_registration_requires_managed_organization(db, url_name):
    assert CoordinatorAuthClient().get(reverse(url_name)).status_code == 403


@pytest.fixture
def coordinator(db):
    client = CoordinatorAuthClient()
    client.orga = OrganizationFactory(address_canton="VD", coordinator=client.user)
    return client


def store_registration(client):
    django_session = client.session
    django_session["new_registration"] = {
        "organization": client.orga.pk,
        "lines": [
            {"date": "2030-03-04", "day_time": "13:30:00", "classes_amount": 2},
            {"date": "2030-03-05", "day_time": "08:30:00", "classes_amount": 1},
        ],
    }
    django_session.save()


def test_register_get_prefills_from_session(coordinator):
    store_registration(coordinator)

    response = coordinator.get(reverse("registration-create"))

    assert response.status_code == 200
    initial = response.context["formset"].initial
    assert initial[0]["date"] == datetime.datetime(2030, 3, 4)
    assert initial[0]["day_time"] == "13:30:00"
    assert initial[1]["classes_amount"] == 1


def test_register_confirm_without_pending_registration(coordinator):
    assert coordinator.get(reverse("registration-confirm")).status_code == 400


def test_register_confirm_get_summarizes_lines(coordinator):
    store_registration(coordinator)

    response = coordinator.get(reverse("registration-confirm"))

    assert response.status_code == 200
    assert response.context["organization"] == coordinator.orga
    assert response.context["total_classes"] == 3
    assert [str(line["day_time"]) for line in response.context["lines"]] == [
        "Après-midi",
        "Matin",
    ]
    assert not response.context["form"].is_bound


def test_register_validate_forbidden_for_coordinator(coordinator):
    assert coordinator.get(reverse("registration-validate")).status_code == 403


def test_register_validate_invalid_post_keeps_other_organizations(db):
    client = StateManagerAuthClient()
    orgas = []
    for _ in range(2):
        orga = OrganizationFactory(
            address_canton="VD", coordinator=CoordinatorAuthClient().user
        )
        RegistrationFactory(
            date=DAY,
            organization=orga,
            coordinator=orga.coordinator,
            day_time="08:30:00",
            classes_amount=1,
        )
        orgas.append(orga)
    registration = orgas[0].registration_set.get()

    response = client.post(
        reverse("registration-validate"),
        data={
            "form-organization-id": orgas[0].pk,
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": registration.pk,
            "form-0-date": "04.03.2030",
            "form-0-day_time": "08:30:00",
            "form-0-classes_amount": "1",
        },
    )

    assert response.status_code == 200
    data = dict(response.context["organizations"])
    assert set(data) == set(orgas)
    assert data[orgas[0]].is_bound
    assert not data[orgas[1]].is_bound
    assert not Session.objects.filter(orga__in=orgas).exists()


def test_admin_missing_languages_lists_untranslated(db):
    activity = QualificationActivityFactory(name="Agilité")
    model_admin = QualificationActivityAdmin(QualificationActivity, admin.site)
    assert model_admin.missing_languages(activity) == "de"


def test_admin_missing_languages_ok_when_complete(db):
    activity = QualificationActivityFactory(name="Agilité")
    activity.set_current_language("de")
    activity.name = "Geschicklichkeit"
    activity.save()
    model_admin = QualificationActivityAdmin(QualificationActivity, admin.site)
    assert "icon-yes.svg" in model_admin.missing_languages(activity)


def test_admin_session_canton(session):
    assert SessionAdmin(Session, admin.site).canton(session) == "VD"
