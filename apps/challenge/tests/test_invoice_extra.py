import csv
import datetime
import io
from decimal import Decimal

from django.urls import reverse

import pytest

from apps.challenge.models import Invoice
from apps.orga.tests.factories import OrganizationFactory
from defivelo.tests.utils import (
    CollaboratorAuthClient,
    PowerUserAuthClient,
    StateManagerAuthClient,
)

from .factories import (
    AnnualStateSettingFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    QualificationFactory,
    SeasonFactory,
    SessionFactory,
)

DAY = datetime.date(2030, 3, 4)


@pytest.fixture
def orga(db):
    return OrganizationFactory(address_canton="VD", name="École du Lac")


@pytest.fixture
def season(db):
    return SeasonFactory(year=2030, month_start=1, n_months=6, cantons=["VD"])


@pytest.fixture
def invoice(season, orga):
    return InvoiceFactory(
        season=season, organization=orga, ref="F-2030-1", status=Invoice.STATUS_DRAFT
    )


def add_line(invoice, day, begin, nb_bikes, nb_participants, cost_bikes, cost_part):
    session = SessionFactory(orga=invoice.organization, day=day, begin=begin)
    return InvoiceLineFactory(
        invoice=invoice,
        session=session,
        nb_bikes=nb_bikes,
        nb_participants=nb_participants,
        cost_bikes=Decimal(cost_bikes),
        cost_participants=Decimal(cost_part),
    )


def detail_url(invoice):
    return reverse(
        "invoice-detail",
        kwargs={
            "seasonpk": invoice.season.pk,
            "orgapk": invoice.organization.pk,
            "invoiceref": invoice.ref,
        },
    )


def test_detail_aggregates_lines_per_day(invoice):
    am = add_line(invoice, DAY, datetime.time(9), 10, 20, "100", "40")
    add_line(invoice, DAY, datetime.time(14), 15, 25, "150", "50")
    next_day = add_line(
        invoice, DAY + datetime.timedelta(days=1), datetime.time(9), 5, 10, "50", "20"
    )

    response = StateManagerAuthClient().get(detail_url(invoice))

    assert response.status_code == 200
    lines = response.context["filtered_lines"]
    assert list(lines) == [DAY, DAY + datetime.timedelta(days=1)]
    first = lines[DAY]
    assert first["obj"] == am
    assert first["line_sum_nb_participants"] == 45
    assert first["line_sum_cost_participants"] == Decimal("90")
    assert first["max_nb_bikes"] == 15
    assert first["line_sum_nb_of_bikes"] == 25
    assert first["max_cost_bikes"] == Decimal("150")
    assert first["cost_bikes"] == Decimal("150")
    assert first["cost_bikes_reduced"] == Decimal("142.50")
    assert first["max_cost_bikes_reduced"] == Decimal("142.50")
    assert first["line_total"] == Decimal("90") + Decimal("142.50")
    assert lines[next_day.historical_session.day]["cost_bikes_reduced"] == Decimal(
        "47.50"
    )
    assert response.context["adjusted_sum_of_bikes"] == 20
    assert response.context["any_line_has_reduction"] is True


def test_detail_without_reduction(invoice):
    add_line(invoice, DAY, datetime.time(9), 10, 20, "100", "40")

    response = StateManagerAuthClient().get(detail_url(invoice))

    day = response.context["filtered_lines"][DAY]
    assert "cost_bikes_reduced" not in day
    assert response.context["any_line_has_reduction"] is False


def test_invoice_str(invoice):
    assert str(invoice).startswith("Facture F-2030-1 pour École du Lac (")
    assert f" / {invoice.season}" in str(invoice)


@pytest.mark.parametrize(
    "status,expected",
    [
        (Invoice.STATUS_DRAFT, "warning"),
        (Invoice.STATUS_VALIDATED, "success"),
        (42, "default"),
    ],
)
def test_invoice_status_class(status, expected):
    assert Invoice(status=status).status_class == expected


def test_adjusted_sum_of_bikes_counts_max_per_day(invoice):
    add_line(invoice, DAY, datetime.time(9), 10, 20, "100", "40")
    add_line(invoice, DAY, datetime.time(14), 12, 20, "120", "40")
    add_line(
        invoice, DAY + datetime.timedelta(days=3), datetime.time(9), 7, 20, "70", "40"
    )

    assert invoice.adjusted_sum_of_bikes == 19


def test_month_of_the_invoice():
    invoice = Invoice(generated_at=datetime.datetime(2030, 3, 4, 12))
    assert invoice.month_of_the_invoice == datetime.date(2030, 3, 4).strftime("%B")


def test_line_str_and_cost(invoice):
    line = add_line(invoice, DAY, datetime.time(9), 10, 20, "100.00", "40.00")

    assert str(line).startswith("F-2030-1: ")
    text = str(line).replace("\xa0", " ")
    assert text.endswith("Vélos: 10 (100.00 CHF) - Participants: 20 (40.00 CHF)")
    assert line.cost == Decimal("140.00")


def test_line_without_session_has_no_recent_history(invoice):
    line = add_line(invoice, DAY, datetime.time(9), 10, 20, "100", "40")
    line.session = None

    assert line.most_recent_historical_session() is None


def test_line_out_of_date_after_session_change(invoice):
    AnnualStateSettingFactory(
        canton="VD", year=2030, cost_per_bike=10, cost_per_participant=2
    )
    session = SessionFactory(orga=invoice.organization, day=DAY)
    QualificationFactory(session=session, n_participants=20, n_bikes=10)
    line = InvoiceLineFactory(invoice=invoice, session=session)
    line.refresh()
    line.save()
    assert line.is_up_to_date

    session.apples = "Golden"
    session.save()
    line.refresh_from_db()
    del line.is_up_to_date

    assert not line.is_up_to_date


def test_line_out_of_date_when_cost_differs(invoice):
    AnnualStateSettingFactory(
        canton="VD", year=2030, cost_per_bike=10, cost_per_participant=2
    )
    session = SessionFactory(orga=invoice.organization, day=DAY)
    QualificationFactory(session=session, n_participants=20, n_bikes=10)
    line = InvoiceLineFactory(invoice=invoice, session=session)
    line.refresh()
    line.cost_bikes += 1

    assert not line.is_up_to_date


def export_url():
    return reverse(
        "invoices-yearly-list-export", kwargs={"year": 2030, "format": "csv"}
    )


def test_yearly_export_contains_only_validated_invoices_of_year(season, orga):
    InvoiceFactory(
        season=season, organization=orga, ref="VALID", status=Invoice.STATUS_VALIDATED
    )
    InvoiceFactory(
        season=season, organization=orga, ref="DRAFT", status=Invoice.STATUS_DRAFT
    )
    InvoiceFactory(
        season=SeasonFactory(year=2029, cantons=["VD"]),
        organization=orga,
        ref="OLD",
        status=Invoice.STATUS_VALIDATED,
    )

    response = PowerUserAuthClient().get(export_url())

    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.content.decode("utf-8"))))
    refs = {cell for row in rows[1:] for cell in row}
    assert "VALID" in refs
    assert "DRAFT" not in refs
    assert "OLD" not in refs


@pytest.mark.xfail(
    strict=True,
    reason="InvoiceListExport declares required_permission but lacks "
    "HasPermissionsMixin, so any logged-in user can export",
)
def test_yearly_export_forbidden_for_collaborator(db):
    assert CollaboratorAuthClient().get(export_url()).status_code == 403
