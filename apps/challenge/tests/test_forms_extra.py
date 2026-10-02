import datetime

from django.core.exceptions import ValidationError

import pytest

from apps.challenge import CHOSEN_AS_REPLACEMENT
from apps.challenge.forms import InvoiceFormQuick, QualificationForm, SessionForm
from apps.challenge.forms.registration import RegistrationValidationFormSet
from apps.challenge.forms.session import nodate_change_warning
from apps.challenge.models import HelperSessionAvailability, Invoice
from apps.orga.tests.factories import OrganizationFactory
from apps.salary.models import Timesheet
from apps.user import FORMATION_M1, FORMATION_M2
from apps.user.tests.factories import UserFactory

from .factories import (
    InvoiceFactory,
    QualificationActivityFactory,
    QualificationFactory,
    RegistrationFactory,
    SeasonFactory,
    SessionFactory,
)

DAY = datetime.date(2030, 3, 4)


@pytest.fixture
def season(db):
    return SeasonFactory(year=2030, month_start=1, n_months=6, cantons=["VD"])


@pytest.fixture
def session(db):
    return SessionFactory(orga__address_canton="VD", day=DAY, begin=datetime.time(9))


def replacement(session, formation=FORMATION_M1, actor_for=None):
    user = UserFactory()
    user.profile.formation = formation
    user.profile.save()
    if actor_for:
        user.profile.actor_for.add(actor_for)
    HelperSessionAvailability.objects.create(
        session=session, helper=user, availability="y", chosen_as=CHOSEN_AS_REPLACEMENT
    )
    return user


def quali_data(session, **extra):
    data = {
        "session": session.pk,
        "name": "Classe A",
        "n_participants": 10,
        "n_helpers": 3,
    }
    data.update(extra)
    return data


def test_qualification_form_for_coordinator_keeps_only_class_fields(session):
    form = QualificationForm(session=session, is_for_coordinator=True)
    assert set(form.fields) == {
        "session",
        "name",
        "class_teacher_fullname",
        "class_teacher_natel",
        "n_participants",
        "n_bikes",
        "n_helmets",
        "n_helpers",
    }


def test_qualification_form_rejects_same_monitor_twice(session):
    user = replacement(session, formation=FORMATION_M2)
    form = QualificationForm(
        data=quali_data(session, leader=user.pk, helpers=[user.pk]), session=session
    )
    assert not form.is_valid()
    assert form.has_error("helpers", "double-helpers")


def test_qualification_form_rejects_unqualified_actor(session):
    actor = replacement(
        session, actor_for=QualificationActivityFactory(category="C", name="X")
    )
    other_activity = QualificationActivityFactory(category="C", name="Y")
    form = QualificationForm(
        data=quali_data(session, actor=actor.pk, activity_C=other_activity.pk),
        session=session,
    )
    assert not form.is_valid()
    assert form.has_error("actor", "unqualified-actor")


def test_qualification_form_accepts_qualified_actor(session):
    activity = QualificationActivityFactory(category="C")
    actor = replacement(session, actor_for=activity)
    form = QualificationForm(
        data=quali_data(session, actor=actor.pk, activity_C=activity.pk),
        session=session,
    )
    assert form.is_valid(), form.errors


def test_qualification_form_rejects_actor_also_helper(session):
    user = replacement(session, actor_for=QualificationActivityFactory(category="C"))
    form = QualificationForm(
        data=quali_data(session, actor=user.pk, helpers=[user.pk]), session=session
    )
    assert not form.is_valid()
    assert form.has_error("actor", "helper-actor")


@pytest.mark.parametrize(
    "extra,code",
    [
        ({"n_bikes": 11}, "too-many-bikes"),
        ({"n_helmets": 11}, "too-many-helmets"),
    ],
)
def test_qualification_form_rejects_more_equipment_than_participants(
    session, extra, code
):
    form = QualificationForm(data=quali_data(session, **extra), session=session)
    assert not form.is_valid()
    assert form.has_error("__all__", code)


def test_qualification_form_deletes_timesheets_of_removed_staff(session):
    helper, actor, kept = UserFactory.create_batch(3)
    quali = QualificationFactory(
        session=session, actor=actor, helpers=[helper, kept], n_participants=10
    )
    for user in (helper, actor, kept):
        Timesheet.objects.create(user=user, date=DAY)
    Timesheet.objects.create(user=helper, date=DAY + datetime.timedelta(days=1))

    form = QualificationForm(
        data=quali_data(session, helpers=[kept.pk]), session=session, instance=quali
    )
    assert form.is_valid(), form.errors

    assert set(Timesheet.objects.values_list("user", "date")) == {
        (kept.pk, DAY),
        (helper.pk, DAY + datetime.timedelta(days=1)),
    }


def test_qualification_form_deletes_timesheets_even_if_form_is_invalid(session):
    helper = UserFactory()
    quali = QualificationFactory(session=session, helpers=[helper])
    Timesheet.objects.create(user=helper, date=DAY)

    form = QualificationForm(
        data=quali_data(session, name=""), session=session, instance=quali
    )

    assert not form.is_valid()
    assert not Timesheet.objects.filter(user=helper).exists()


def session_form(season, session, day):
    return SessionForm(
        data={"orga": session.orga.pk, "day": day, "begin": "09:00"},
        season=season,
        instance=session,
    )


def test_session_form_rejects_day_outside_season(season, session):
    form = session_form(season, session, "01.09.2030")
    assert not form.is_valid()
    assert "La session doit être dans le mois" in form.errors["day"][0]


def test_session_form_rejects_day_change_with_timesheets(season, session):
    leader = UserFactory()
    QualificationFactory(session=session, leader=leader)
    Timesheet.objects.create(user=leader, date=DAY)

    form = session_form(season, session, "05.03.2030")

    assert not form.is_valid()
    assert form.errors["day"] == [str(nodate_change_warning)]
    assert form.fields["day"].widget.attrs["readonly"] is True


def invoice_form(season, orga):
    return InvoiceFormQuick(
        data={
            "title": "",
            "status": Invoice.STATUS_DRAFT,
            "organization": orga.pk,
            "season": season.pk,
        }
    )


def test_invoice_form_increments_largest_ref(season):
    orga = OrganizationFactory(address_canton="VD")
    InvoiceFactory(season=season, organization=orga, ref="DV30105")
    InvoiceFactory(season=season, organization=orga, ref="DV29999")

    form = invoice_form(season, orga)
    assert form.is_valid(), form.errors

    assert form.save().ref == "DV30106"


def test_invoice_form_starts_at_100(season):
    orga = OrganizationFactory(address_canton="VD")
    form = invoice_form(season, orga)
    assert form.is_valid(), form.errors

    assert form.save().ref == "DV30100"


@pytest.mark.xfail(
    raises=UnboundLocalError,
    strict=True,
    reason="forms/invoices.py:53-64: when the ref space is exhausted the for "
    "loop never runs and the error message references an unbound `ref`",
)
def test_invoice_form_exhausted_refs_raise_validation_error(season):
    orga = OrganizationFactory(address_canton="VD")
    InvoiceFactory(season=season, organization=orga, ref="DV30998")
    form = invoice_form(season, orga)
    assert form.is_valid(), form.errors

    with pytest.raises(ValidationError):
        form.save()


def test_registration_validation_ignores_deleted_forms_for_overlap(db):
    coordinator = UserFactory()
    orga = OrganizationFactory(coordinator=coordinator)
    registrations = [
        RegistrationFactory(
            date=DAY,
            organization=orga,
            coordinator=coordinator,
            day_time="08:30:00",
            classes_amount=1,
        )
        for _ in range(2)
    ]
    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
    }
    for i, registration in enumerate(registrations):
        data.update(
            {
                f"form-{i}-id": registration.pk,
                f"form-{i}-date": "04.03.2030",
                f"form-{i}-day_time": "08:30:00",
                f"form-{i}-classes_amount": "1",
                f"form-{i}-is_validated": "true",
            }
        )
    data["form-1-DELETE"] = "on"

    formset = RegistrationValidationFormSet(organization=orga, data=data)

    assert formset.is_valid(), formset.errors
