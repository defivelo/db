import datetime

import pytest
from rolepermissions.roles import assign_role

from apps.challenge.tests.factories import QualificationFactory, SessionFactory
from apps.orga.tests.factories import OrganizationFactory
from apps.salary.forms import (
    ControlTimesheetForm,
    MonthlyCantonalValidationForm,
    TimesheetForm,
)
from apps.salary.models import MonthlyCantonalValidationUrl, Timesheet
from apps.user.tests.factories import UserFactory

from .factories import MonthlyCantonalValidationFactory, ValidatedTimesheetFactory

DAY = datetime.date(2019, 4, 12)


@pytest.fixture
def monitor(db):
    user = UserFactory()
    QualificationFactory(
        actor=user,
        session=SessionFactory(day=DAY, orga=OrganizationFactory(address_canton="VD")),
    )
    return user


def make_validator(role):
    user = UserFactory()
    assign_role(user, role)
    return user


def timesheet_data(**overrides):
    data = {
        "date": DAY.isoformat(),
        "time_helper": "4.5",
        "actor_count": "1",
        "leader_count": "0",
        "overtime": "0",
        "traveltime": "1",
        "comments": "",
    }
    data.update(overrides)
    return data


def timesheet_initial(validated):
    return {
        "date": DAY,
        "time_helper": 4.5,
        "actor_count": 1,
        "leader_count": 0,
        "overtime": 0,
        "traveltime": 1,
        "validated": validated,
        "ignore": False,
        "comments": "",
    }


def test_timesheet_form_validated_disables_all_fields(monitor):
    form = TimesheetForm(
        selected_user=monitor,
        validator=monitor,
        initial=timesheet_initial(validated=True),
    )
    assert all(field.disabled for field in form.fields.values())


def test_timesheet_form_not_validated_hides_ignore(monitor):
    form = TimesheetForm(
        selected_user=monitor,
        validator=monitor,
        initial=timesheet_initial(validated=False),
    )
    assert not form.fields["overtime"].disabled
    assert form.fields["ignore"].widget.is_hidden


def test_timesheet_form_rejects_day_without_qualif(monitor):
    form = TimesheetForm(
        selected_user=monitor,
        validator=monitor,
        initial=timesheet_initial(validated=False),
        data=timesheet_data(date="2019-04-13"),
    )
    assert not form.is_valid()
    assert "aucune qualif" in str(form.non_field_errors())


def test_timesheet_form_save_with_errors_raises(monitor):
    form = TimesheetForm(
        selected_user=monitor,
        validator=monitor,
        initial=timesheet_initial(validated=False),
        data=timesheet_data(overtime="1"),
    )
    assert not form.is_valid()
    assert "comments" in form.errors
    with pytest.raises(ValueError):
        form.save()
    assert not Timesheet.objects.exists()


def test_control_form_validated_disabled_for_state_manager(monitor):
    form = ControlTimesheetForm(
        selected_user=monitor,
        validator=make_validator("state_manager"),
        initial=timesheet_initial(validated=True),
    )
    assert all(field.disabled for field in form.fields.values())
    assert "disabled" not in form.fields["ignore"].widget.attrs


def test_control_form_validated_editable_for_power_user(monitor):
    form = ControlTimesheetForm(
        selected_user=monitor,
        validator=make_validator("power_user"),
        initial=timesheet_initial(validated=True),
    )
    assert not any(field.disabled for field in form.fields.values())


def test_control_form_validates_timesheet(monitor):
    validator = make_validator("state_manager")
    form = ControlTimesheetForm(
        selected_user=monitor,
        validator=validator,
        initial=timesheet_initial(validated=False),
        data=timesheet_data(validated="on"),
    )
    assert form.is_valid(), form.errors
    timesheet = form.save()
    assert timesheet.validated_by == validator
    assert timesheet.validated_at is not None


def test_power_user_can_unvalidate_timesheet(monitor):
    ValidatedTimesheetFactory(user=monitor, date=DAY)
    form = ControlTimesheetForm(
        selected_user=monitor,
        validator=make_validator("power_user"),
        initial=timesheet_initial(validated=True),
        data=timesheet_data(),
    )
    assert form.is_valid(), form.errors
    timesheet = form.save()
    assert timesheet.validated_at is None
    assert timesheet.validated_by is None


def test_state_manager_cannot_unvalidate_timesheet(monitor):
    original = ValidatedTimesheetFactory(user=monitor, date=DAY)
    form = ControlTimesheetForm(
        selected_user=monitor,
        validator=make_validator("state_manager"),
        initial=timesheet_initial(validated=True),
        data=timesheet_data(),
    )
    assert form.is_valid(), form.errors
    timesheet = form.save()
    assert timesheet.validated_at is not None
    assert timesheet.validated_by == original.validated_by


@pytest.fixture
def mcv(db):
    return MonthlyCantonalValidationFactory(canton="VD", date=DAY)


@pytest.fixture
def urls(db):
    MonthlyCantonalValidationUrl.objects.all().delete()
    return [
        MonthlyCantonalValidationUrl.objects.create(
            name=f"URL {i}", url=f"https://{i}.example.com"
        )
        for i in range(2)
    ]


def mcv_form(mcv, urls, data=None, validated=False, timesheets_ok=True, **kwargs):
    return MonthlyCantonalValidationForm(
        validator=kwargs.get("validator") or UserFactory(),
        urls=urls,
        timesheets_statuses={"VD": timesheets_ok},
        instance=mcv,
        initial={"validated": validated},
        data=data,
    )


def test_mcv_form_has_url_checkboxes_first(mcv, urls):
    form = mcv_form(mcv, urls)
    assert list(form.fields) == [
        "timesheets_checked",
        f"url_{urls[0].pk}",
        f"url_{urls[1].pk}",
        "validated",
    ]


def test_mcv_form_url_label_falls_back_to_url(mcv, urls):
    urls[1].label = "Nice label"
    urls[1].save()
    form = mcv_form(mcv, urls)
    assert "https://0.example.com</a>" in form.fields[f"url_{urls[0].pk}"].help_text
    assert "Nice label</a>" in form.fields[f"url_{urls[1].pk}"].help_text


def test_mcv_form_requires_all_urls_ticked(mcv, urls):
    form = mcv_form(mcv, urls, data={"validated": "on", f"url_{urls[0].pk}": "on"})
    assert not form.is_valid()
    assert list(form.errors) == [f"url_{urls[1].pk}"]


def test_mcv_form_requires_timesheets_validated(mcv, urls):
    form = mcv_form(
        mcv,
        urls,
        timesheets_ok=False,
        data={"validated": "on", **{f"url_{u.pk}": "on" for u in urls}},
    )
    assert not form.is_valid()
    assert list(form.errors) == ["timesheets_checked"]


def test_mcv_form_validates_and_saves_urls(mcv, urls):
    validator = UserFactory()
    form = mcv_form(
        mcv,
        urls,
        validator=validator,
        data={"validated": "on", **{f"url_{u.pk}": "on" for u in urls}},
    )
    assert form.is_valid(), form.errors
    saved = form.save()
    saved.refresh_from_db()
    assert saved.validated_by == validator
    assert saved.validated is True


def test_mcv_form_save_unticks_urls(mcv, urls):
    mcv.validated_urls.set(urls)
    form = mcv_form(mcv, urls, data={f"url_{urls[0].pk}": "on"})
    assert form.is_valid(), form.errors
    form.save()
    assert list(mcv.validated_urls.all()) == [urls[0]]


def test_mcv_form_save_ignores_non_numeric_url_fields(mcv, urls):
    form = mcv_form(mcv, urls, data={})
    form.fields["url_bogus"] = form.fields[f"url_{urls[0].pk}"]
    assert form.is_valid(), form.errors
    form.save()
    assert not mcv.validated_urls.exists()


def test_mcv_form_validated_disables_all_fields(mcv, urls):
    form = mcv_form(mcv, urls, validated=True)
    assert all(field.disabled for field in form.fields.values())


def test_mcv_form_cannot_be_unvalidated_once_validated(mcv, urls):
    validator = UserFactory()
    mcv.validated_at = datetime.datetime(2019, 5, 1, tzinfo=datetime.timezone.utc)
    mcv.validated_by = validator
    mcv.save()
    mcv.validated_urls.set(urls)
    form = mcv_form(mcv, urls, validated=True, data={})
    assert form.is_valid(), form.errors
    assert "validated_at" not in form.cleaned_data
    form.save()
    mcv.refresh_from_db()
    assert mcv.validated_by == validator
