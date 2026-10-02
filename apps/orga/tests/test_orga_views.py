import json

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.urls import reverse

import pytest

from apps.orga.models import Organization
from apps.orga.tests.factories import OrganizationFactory
from apps.orga.views import OrganizationAutocomplete, OrganizationFilterSet
from defivelo.tests.utils import (
    CollaboratorAuthClient,
    CoordinatorAuthClient,
    PowerUserAuthClient,
)

pytestmark = pytest.mark.django_db


def test_filter_wide_with_empty_value_returns_queryset_untouched():
    OrganizationFactory.create_batch(2)
    qs = Organization.objects.all()
    assert OrganizationFilterSet.filter_wide(qs, "q", "") is qs


def test_filter_wide_matches_unaccented_name():
    match = OrganizationFactory(name="Collège Sainte-Croix")
    OrganizationFactory(name="Autre")
    qs = OrganizationFilterSet.filter_wide(Organization.objects.all(), "q", "college")
    assert list(qs) == [match]


def test_autocomplete_filters_with_query():
    match = OrganizationFactory(name="Zyxwv")
    OrganizationFactory(name="Autre")
    response = PowerUserAuthClient().get(
        reverse("organization-autocomplete"), {"q": "zyx"}
    )
    assert response.status_code == 200
    ids = [r["id"] for r in json.loads(response.content)["results"]]
    assert ids == [str(match.pk)]


def test_autocomplete_queryset_denied_without_permission():
    client = CollaboratorAuthClient()
    request = RequestFactory().get("/")
    request.user = client.user
    view = OrganizationAutocomplete()
    view.setup(request)
    view.q = ""
    with pytest.raises(PermissionDenied):
        view.get_queryset()


def test_coordinator_without_organizations_cannot_edit():
    orga = OrganizationFactory()
    response = CoordinatorAuthClient().get(
        reverse("organization-update", kwargs={"pk": orga.pk})
    )
    assert response.status_code == 403
