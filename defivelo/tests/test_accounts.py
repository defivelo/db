"""
Functional tests of the django-allauth flows used by the intranet.

They drive the real URLs, templates and emails so that an allauth upgrade
breaking login, password reset or email confirmation is caught here.
"""

import re
from urllib.parse import urlparse

from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.urls import reverse

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import get_adapter as get_socialaccount_adapter

from apps.user.management.commands.createsuperuser import ProxyUser
from apps.user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

EMAIL = "jane.doe@example.com"
PASSWORD = "Old-Secret-2026!"
NEW_PASSWORD = "New-Secret-2026!"
LOGIN_CODE_PATH = "/accounts/login/code/"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    # allauth rate limits (failed logins, confirmation mails) live in the cache
    cache.clear()
    yield
    cache.clear()


def make_user(email=EMAIL, verified=True, is_active=True, **kwargs):
    user = UserFactory(
        email=email, first_name="Jane", last_name="Doe", is_active=is_active, **kwargs
    )
    user.set_password(PASSWORD)
    user.save()
    EmailAddress.objects.create(user=user, email=email, verified=verified, primary=True)
    return user


def logged_in_user_pk(client):
    pk = client.session.get(SESSION_KEY)
    return int(pk) if pk else None


def login(client, email=EMAIL, password=PASSWORD, **extra):
    return client.post(
        reverse("account_login"), {"login": email, "password": password, **extra}
    )


def link_in(message):
    match = re.search(r"https?://\S+", message.body)
    assert match, message.body
    return urlparse(match.group(0)).path


def template_names(response):
    return [t.name for t in response.templates]


@pytest.mark.parametrize(
    "name",
    [
        "account_email_verification_sent",
        "account_inactive",
        "account_reset_password_done",
        "account_reset_password_from_key_done",
        "account_signup",
    ],
)
def test_allauth_pages_use_project_layout(client, name):
    response = client.get(reverse(name))

    assert response.status_code == 200
    assert "account/base.html" in template_names(response)
    assert reverse("account_signup") not in response.content.decode()


class TestLogin:
    def test_login_page_uses_project_template(self, client):
        response = client.get(reverse("account_login"))

        assert response.status_code == 200
        assert "account/login.html" in template_names(response)
        assert reverse("account_reset_password") in response.content.decode()

    def test_anonymous_user_is_sent_to_login(self, client):
        response = client.get(reverse("home"))

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))
        assert "next=/" in response.url

    def test_login_with_verified_email(self, client):
        user = make_user()

        response = login(client)

        assert response.status_code == 302
        assert response.url == "/"
        assert logged_in_user_pk(client) == user.pk

    def test_login_redirects_to_next(self, client):
        make_user()

        response = login(client, next="/fr/user/")

        assert response.url == "/fr/user/"

    def test_login_ignores_email_case(self, client):
        user = make_user()

        login(client, email=EMAIL.upper())

        assert logged_in_user_pk(client) == user.pk

    @pytest.mark.parametrize(
        "email,password",
        [(EMAIL, "wrong-password"), ("nobody@example.com", PASSWORD)],
    )
    def test_login_with_bad_credentials_is_refused(self, client, email, password):
        make_user()

        response = login(client, email=email, password=password)

        assert response.status_code == 200
        assert response.context["form"].errors
        assert logged_in_user_pk(client) is None

    def test_login_without_usable_password_is_refused(self, client):
        UserFactory(email=EMAIL, is_active=True)

        login(client)

        assert logged_in_user_pk(client) is None

    def test_inactive_user_is_refused(self, client):
        make_user(is_active=False)

        response = login(client)

        assert response.url == reverse("account_inactive")
        assert logged_in_user_pk(client) is None

    def test_unverified_email_requires_confirmation(self, client, mailoutbox):
        make_user(verified=False)

        response = login(client)

        assert response.url == reverse("account_email_verification_sent")
        assert logged_in_user_pk(client) is None
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == [EMAIL]


class TestLogout:
    def test_get_asks_for_confirmation(self, client):
        user = make_user()
        login(client)

        response = client.get(reverse("account_logout"))

        assert response.status_code == 200
        assert "account/logout.html" in template_names(response)
        assert logged_in_user_pk(client) == user.pk

    def test_post_logs_out(self, client):
        make_user()
        login(client)

        response = client.post(reverse("account_logout"))

        assert response.status_code == 302
        assert logged_in_user_pk(client) is None


class TestSignup:
    def test_signup_is_closed(self, client):
        response = client.get(reverse("account_signup"))

        assert "account/signup_closed.html" in template_names(response)

    def test_signup_post_creates_no_user(self, client):
        client.post(
            reverse("account_signup"),
            {"email": EMAIL, "password1": PASSWORD, "password2": PASSWORD},
        )

        assert not get_user_model().objects.filter(email=EMAIL).exists()

    def test_login_page_offers_no_signup_nor_login_code(self, client):
        content = client.get(reverse("account_login")).content.decode()

        assert reverse("account_signup") not in content
        assert LOGIN_CODE_PATH not in content

    def test_social_signup_is_closed(self, rf):
        request = rf.get("/")

        assert get_socialaccount_adapter(request).is_open_for_signup(request, None) is (
            False
        )

    def test_social_signup_page_creates_no_user(self, client):
        response = client.post(
            reverse("socialaccount_signup"),
            {"email": EMAIL, "password1": PASSWORD, "password2": PASSWORD},
        )

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))
        assert not get_user_model().objects.filter(email=EMAIL).exists()

    def test_login_by_code_is_disabled(self, client, mailoutbox):
        make_user()

        response = client.post(LOGIN_CODE_PATH, {"email": EMAIL})

        assert response.status_code == 404
        assert mailoutbox == []


class TestPasswordReset:
    def request_reset(self, client, email=EMAIL):
        return client.post(reverse("account_reset_password"), {"email": email})

    def set_password(self, client, path, password1=NEW_PASSWORD, password2=None):
        # allauth moves the key from the URL to the session before showing the form
        response = client.get(path)
        assert response.status_code == 302
        set_password_url = response.url
        response = client.get(set_password_url)
        assert response.status_code == 200
        assert "account/password_reset_from_key.html" in template_names(response)
        return client.post(
            set_password_url,
            {"password1": password1, "password2": password2 or password1},
        )

    def test_reset_page_uses_project_template(self, client):
        response = client.get(reverse("account_reset_password"))

        assert response.status_code == 200
        assert "account/password_reset.html" in template_names(response)

    def test_full_reset_flow(self, client, mailoutbox):
        user = make_user()

        response = self.request_reset(client)

        assert response.url == reverse("account_reset_password_done")
        assert len(mailoutbox) == 1
        message = mailoutbox[0]
        assert message.to == [EMAIL]
        assert "Réinitialisation du mot de passe" in message.subject
        assert link_in(message).startswith("/accounts/password/reset/key/")

        response = self.set_password(client, link_in(message))

        assert response.url == reverse("account_reset_password_from_key_done")
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)
        assert logged_in_user_pk(client) is None

        login(client, password=PASSWORD)
        assert logged_in_user_pk(client) is None
        login(client, password=NEW_PASSWORD)
        assert logged_in_user_pk(client) == user.pk

    def test_reset_link_works_only_once(self, client, mailoutbox):
        make_user()
        self.request_reset(client)
        path = link_in(mailoutbox[0])
        self.set_password(client, path)

        response = client.get(path, follow=True)

        assert response.context["token_fail"] is True

    def test_tampered_reset_link_fails(self, client, mailoutbox):
        make_user()
        self.request_reset(client)
        path = link_in(mailoutbox[0])
        tampered = path.rstrip("/")[:-3] + "xyz/"

        response = client.get(tampered, follow=True)

        assert response.context["token_fail"] is True

    def test_mismatched_passwords_keep_old_password(self, client, mailoutbox):
        user = make_user()
        self.request_reset(client)

        response = self.set_password(
            client, link_in(mailoutbox[0]), password2="Something-Else-2026!"
        )

        assert response.status_code == 200
        assert response.context["form"].errors
        user.refresh_from_db()
        assert user.check_password(PASSWORD)

    def test_unknown_email_does_not_reveal_accounts(self, client, mailoutbox):
        response = self.request_reset(client, email="nobody@example.com")

        assert response.url == reverse("account_reset_password_done")
        assert len(mailoutbox) == 1
        message = mailoutbox[0]
        assert message.to == ["nobody@example.com"]
        assert "Réinitialisation du mot de passe" in message.subject
        assert "aucun compte n'est associé à l'adresse nobody@example.com" in (
            message.body
        )
        assert "/accounts/password/reset/key/" not in message.body
        assert reverse("account_signup") not in message.body


class TestEmailConfirmation:
    def confirmation_link(self, client, mailoutbox):
        login(client)
        assert len(mailoutbox) == 1
        return link_in(mailoutbox[0])

    def test_confirmation_email_content(self, client, mailoutbox):
        make_user(verified=False)

        path = self.confirmation_link(client, mailoutbox)

        message = mailoutbox[0]
        assert "Confirmer l'adresse e-mail" in message.subject
        assert "Jane Doe" in message.body
        assert path.startswith("/accounts/confirm-email/")

    def test_confirming_verifies_and_logs_in(self, client, mailoutbox):
        user = make_user(verified=False)
        path = self.confirmation_link(client, mailoutbox)

        response = client.get(path)

        assert response.status_code == 200
        assert "account/email_confirm.html" in template_names(response)
        assert response.context["confirmation"] is not None

        response = client.post(path)

        assert response.url == "/"
        assert EmailAddress.objects.get(user=user, email=EMAIL).verified
        assert logged_in_user_pk(client) == user.pk

    def test_invalid_key_shows_expired_message(self, client):
        response = client.get(reverse("account_confirm_email", args=["not-a-key"]))

        assert "account/email_confirm.html" in template_names(response)
        assert response.context["confirmation"] is None


class TestEmailManagement:
    NEW_EMAIL = "jane.new@example.com"

    @pytest.fixture
    def user(self, client):
        user = make_user()
        login(client)
        return user

    def add_email(self, client):
        return client.post(
            reverse("account_email"), {"action_add": "", "email": self.NEW_EMAIL}
        )

    def test_page_lists_addresses(self, client, user):
        response = client.get(reverse("account_email"))

        assert response.status_code == 200
        assert "account/email.html" in template_names(response)
        assert EMAIL in response.content.decode()

    def test_add_email_sends_confirmation(self, client, user, mailoutbox):
        self.add_email(client)

        added = EmailAddress.objects.get(user=user, email=self.NEW_EMAIL)
        assert not added.verified
        assert not added.primary
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == [self.NEW_EMAIL]

    def test_confirmed_email_can_become_primary(self, client, user, mailoutbox):
        self.add_email(client)
        client.post(link_in(mailoutbox[0]))

        client.post(
            reverse("account_email"), {"action_primary": "", "email": self.NEW_EMAIL}
        )

        user.refresh_from_db()
        assert user.email == self.NEW_EMAIL
        assert EmailAddress.objects.get(user=user, primary=True).email == (
            self.NEW_EMAIL
        )

    def test_unverified_email_cannot_become_primary(self, client, user):
        self.add_email(client)

        client.post(
            reverse("account_email"), {"action_primary": "", "email": self.NEW_EMAIL}
        )

        user.refresh_from_db()
        assert user.email == EMAIL

    def test_resend_confirmation(self, client, user, mailoutbox):
        self.add_email(client)
        cache.clear()

        client.post(
            reverse("account_email"), {"action_send": "", "email": self.NEW_EMAIL}
        )

        assert len(mailoutbox) == 2
        assert mailoutbox[1].to == [self.NEW_EMAIL]

    def test_remove_secondary_email(self, client, user):
        self.add_email(client)

        client.post(
            reverse("account_email"), {"action_remove": "", "email": self.NEW_EMAIL}
        )

        assert list(
            EmailAddress.objects.filter(user=user).values_list("email", flat=True)
        ) == [EMAIL]


class TestPasswordChange:
    def change(self, client, oldpassword=PASSWORD):
        return client.post(
            reverse("account_change_password"),
            {
                "oldpassword": oldpassword,
                "password1": NEW_PASSWORD,
                "password2": NEW_PASSWORD,
            },
        )

    def test_anonymous_is_sent_to_login(self, client):
        response = client.get(reverse("account_change_password"))

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))

    def test_change_password(self, client):
        user = make_user()
        login(client)

        response = client.get(reverse("account_change_password"))
        assert "account/password_change.html" in template_names(response)
        response = self.change(client)

        assert response.status_code == 302
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)
        assert logged_in_user_pk(client) == user.pk

    def test_wrong_old_password_is_refused(self, client):
        user = make_user()
        login(client)

        response = self.change(client, oldpassword="wrong-password")

        assert response.status_code == 200
        assert response.context["form"].has_error("oldpassword")
        user.refresh_from_db()
        assert user.check_password(PASSWORD)


class TestProjectIntegration:
    def test_emailed_credentials_allow_login(self, client, mailoutbox):
        user = UserFactory(email=EMAIL, first_name="Jane", last_name="Doe")
        sender = UserFactory()

        user.profile.send_credentials(
            {
                "fromuser": sender,
                "current_site": Site.objects.get_current(),
                "login_uri": "https://intranet.example.com/accounts/login/",
            }
        )

        assert len(mailoutbox) == 1
        password = re.search(r"Mot de passe\s*: (\S+)", mailoutbox[0].body).group(1)
        response = login(client, password=password)
        assert response.url == "/"
        assert logged_in_user_pk(client) == user.pk

    def test_createsuperuser_can_login(self, client):
        user = ProxyUser.objects.create_superuser("admin", EMAIL, PASSWORD)

        login(client)

        assert logged_in_user_pk(client) == user.pk
        assert EmailAddress.objects.get(user=user).verified
