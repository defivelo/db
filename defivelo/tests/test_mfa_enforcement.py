"""
Mandatory two-factor authentication for PowerUsers and superusers.
"""

from django.urls import reverse

import pytest
from allauth.mfa.models import Authenticator

from defivelo.tests.utils import (
    CollaboratorAuthClient,
    CoordinatorAuthClient,
    PowerUserAuthClient,
    StateManagerAuthClient,
    SuperUserAuthClient,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _enable_mfa_enforcement(settings):
    settings.MFA_ENFORCEMENT_ENABLED = True


def _give_totp(client):
    Authenticator.objects.create(
        user=client.user, type=Authenticator.Type.TOTP, data={}
    )


def _give_webauthn(client):
    Authenticator.objects.create(
        user=client.user, type=Authenticator.Type.WEBAUTHN, data={}
    )


def _give_recovery_codes(client):
    Authenticator.objects.create(
        user=client.user, type=Authenticator.Type.RECOVERY_CODES, data={}
    )


@pytest.mark.parametrize("make_client", [PowerUserAuthClient, SuperUserAuthClient])
def test_mfa_required_role_without_authenticator_is_redirected(make_client):
    client = make_client()
    response = client.get(reverse("home"))
    assert response.status_code == 302
    assert response.url == reverse("mfa_index")


@pytest.mark.parametrize("make_client", [PowerUserAuthClient, SuperUserAuthClient])
def test_mfa_required_role_with_totp_is_not_redirected(make_client):
    client = make_client()
    _give_totp(client)
    response = client.get(reverse("home"))
    assert response.status_code == 200


@pytest.mark.parametrize("make_client", [PowerUserAuthClient, SuperUserAuthClient])
def test_mfa_required_role_with_webauthn_is_not_redirected(make_client):
    client = make_client()
    _give_webauthn(client)
    response = client.get(reverse("home"))
    assert response.status_code == 200


@pytest.mark.parametrize("make_client", [PowerUserAuthClient, SuperUserAuthClient])
def test_mfa_required_role_with_only_recovery_codes_is_still_redirected(make_client):
    client = make_client()
    _give_recovery_codes(client)
    response = client.get(reverse("home"))
    assert response.status_code == 302
    assert response.url == reverse("mfa_index")


@pytest.mark.parametrize(
    "make_client",
    [CollaboratorAuthClient, StateManagerAuthClient, CoordinatorAuthClient],
)
def test_other_roles_are_never_redirected(make_client):
    client = make_client()
    response = client.get(reverse("home"))
    assert response.status_code == 200


def test_noncompliant_poweruser_can_still_reach_mfa_setup_and_logout():
    client = PowerUserAuthClient()
    assert client.get(reverse("mfa_index")).status_code == 200
    assert client.get(reverse("mfa_activate_totp")).status_code in (200, 302)
    assert client.post(reverse("account_logout")).status_code in (200, 302)


def test_anonymous_admin_login_redirects_to_account_login():
    from django.test import Client

    response = Client().get("/admin/login/?next=/admin/")
    assert response.status_code == 302
    assert response.url == f"{reverse('account_login')}?next=/admin/"


def test_compliant_poweruser_can_reach_admin():
    client = PowerUserAuthClient()
    _give_totp(client)
    client.user.is_staff = True
    client.user.save()
    response = client.get("/admin/")
    assert response.status_code == 200


def test_authenticated_staff_hitting_admin_login_reaches_admin_index():
    client = PowerUserAuthClient()
    _give_totp(client)
    client.user.is_staff = True
    client.user.save()
    response = client.get("/admin/login/")
    assert response.status_code == 302
    assert response.url == reverse("admin:index")


def test_authenticated_non_staff_hitting_admin_does_not_loop():
    client = CollaboratorAuthClient()
    assert client.user.is_staff is False
    response = client.get("/admin/", follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[-1][0] == reverse("home")
