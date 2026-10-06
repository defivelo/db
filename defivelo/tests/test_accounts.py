"""
Functional tests of the django-allauth flows used by the intranet.

They drive the real URLs and emails and assert the rendered HTML, so that an
allauth upgrade breaking login, password reset or email confirmation, or
changing what users see on those pages, is caught here.
"""

import re
from smtplib import SMTPException
from unittest.mock import patch
from urllib.parse import urlparse

from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.urls import reverse

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import get_adapter as get_socialaccount_adapter
from bs4 import BeautifulSoup

from apps.user.management.commands.createsuperuser import ProxyUser
from apps.user.models import UserProfile
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


def squash(text):
    return " ".join(text.split())


def intranet_page(response, heading):
    """
    Parse an allauth page and check it is rendered inside the intranet layout,
    with the expected heading and without any way to sign up.
    """
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.select_one("#dv-navbar-logo"), "page is not in the intranet layout"
    assert squash(soup.h1.get_text()) == heading
    assert not soup.find("a", href=reverse("account_signup"))
    return soup


def main_text(soup):
    return squash(soup.select_one("[role=main]").get_text())


def form_fields(soup, action):
    form = soup.find("form", action=action)
    assert form, f"no form posting to {action}"
    return {field.get("name") for field in form.select("input, button")}


class TestLogin:
    def test_login_page(self, client):
        soup = intranet_page(client.get(reverse("account_login")), "Connexion")

        assert {"login", "password"} <= form_fields(soup, reverse("account_login"))
        reset = soup.find("a", href=reverse("account_reset_password"))
        assert squash(reset.get_text()) == "Mot de passe oublié ?"

    def test_anonymous_user_is_sent_to_login(self, client):
        response = client.get(reverse("home"), follow=True)

        assert response.redirect_chain[0][0].startswith(reverse("account_login"))
        assert "next=/" in response.redirect_chain[0][0]
        intranet_page(response, "Connexion")

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

        soup = intranet_page(login(client, email=email, password=password), "Connexion")

        assert "L’adresse e-mail ou le mot de passe sont incorrects." in main_text(soup)
        assert logged_in_user_pk(client) is None

    def test_login_without_usable_password_is_refused(self, client):
        UserFactory(email=EMAIL, is_active=True)

        soup = intranet_page(login(client), "Connexion")

        assert "L’adresse e-mail ou le mot de passe sont incorrects." in main_text(soup)
        assert logged_in_user_pk(client) is None

    def test_inactive_user_is_refused(self, client):
        make_user(is_active=False)

        response = client.post(
            reverse("account_login"),
            {"login": EMAIL, "password": PASSWORD},
            follow=True,
        )

        assert response.redirect_chain == [(reverse("account_inactive"), 302)]
        soup = intranet_page(response, "Compte inactif")
        assert "Ce compte est inactif." in main_text(soup)
        assert logged_in_user_pk(client) is None

    def test_unverified_email_requires_confirmation(self, client, mailoutbox):
        make_user(verified=False)

        response = client.post(
            reverse("account_login"),
            {"login": EMAIL, "password": PASSWORD},
            follow=True,
        )

        assert response.redirect_chain == [
            (reverse("account_email_verification_sent"), 302)
        ]
        soup = intranet_page(response, "Vérifiez votre adresse e-mail")
        assert "Nous vous avons envoyé un e-mail pour validation." in main_text(soup)
        assert logged_in_user_pk(client) is None
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == [EMAIL]


class TestLogout:
    def test_get_asks_for_confirmation(self, client):
        user = make_user()
        login(client)

        soup = intranet_page(client.get(reverse("account_logout")), "Se Déconnecter")

        assert "Êtes-vous sûr de vouloir vous déconnecter ?" in main_text(soup)
        assert form_fields(soup, reverse("account_logout"))
        assert logged_in_user_pk(client) == user.pk

    def test_post_logs_out(self, client):
        make_user()
        login(client)

        response = client.post(reverse("account_logout"))

        assert response.status_code == 302
        assert logged_in_user_pk(client) is None


class TestSignup:
    def test_signup_is_closed(self, client):
        soup = intranet_page(
            client.get(reverse("account_signup")), "Inscriptions fermées"
        )

        assert "les inscriptions sont actuellement fermées" in main_text(soup)
        assert not soup.select("[role=main] form")

    def test_signup_post_creates_no_user(self, client):
        client.post(
            reverse("account_signup"),
            {"email": EMAIL, "password1": PASSWORD, "password2": PASSWORD},
        )

        assert not get_user_model().objects.filter(email=EMAIL).exists()

    def test_login_page_offers_no_login_code(self, client):
        content = client.get(reverse("account_login")).content.decode()

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
        return client.post(
            reverse("account_reset_password"), {"email": email}, follow=True
        )

    def set_password(self, client, path, password1=NEW_PASSWORD, password2=None):
        # allauth moves the key from the URL to the session before showing the form
        response = client.get(path)
        assert response.status_code == 302
        set_password_url = response.url
        soup = intranet_page(client.get(set_password_url), "Modifier le mot de passe")
        assert {"password1", "password2"} <= form_fields(soup, ".")
        return client.post(
            set_password_url,
            {"password1": password1, "password2": password2 or password1},
            follow=True,
        )

    def assert_reset_requested(self, response):
        assert response.redirect_chain == [
            (reverse("account_reset_password_done"), 302)
        ]
        soup = intranet_page(response, "Réinitialisation du mot de passe")
        assert "Nous vous avons envoyé un email de vérification." in main_text(soup)

    def test_reset_page(self, client):
        soup = intranet_page(
            client.get(reverse("account_reset_password")),
            "Réinitialisation du mot de passe",
        )

        assert "Mot de passe oublié ?" in main_text(soup)
        assert "email" in form_fields(soup, reverse("account_reset_password"))

    def test_full_reset_flow(self, client, mailoutbox):
        user = make_user()

        self.assert_reset_requested(self.request_reset(client))
        assert len(mailoutbox) == 1
        message = mailoutbox[0]
        assert message.to == [EMAIL]
        assert "Réinitialisation du mot de passe" in message.subject
        assert link_in(message).startswith("/accounts/password/reset/key/")

        response = self.set_password(client, link_in(message))

        assert response.redirect_chain[-1] == (
            reverse("account_reset_password_from_key_done"),
            302,
        )
        soup = intranet_page(response, "Modifier le mot de passe")
        assert "Votre mot de passe a été modifié." in main_text(soup)
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)
        assert logged_in_user_pk(client) is None

        login(client, password=PASSWORD)
        assert logged_in_user_pk(client) is None
        login(client, password=NEW_PASSWORD)
        assert logged_in_user_pk(client) == user.pk

    def assert_token_fail(self, response):
        soup = intranet_page(response, "Mauvais jeton d'identification")
        assert "Le lien de réinitialisation du mot de passe est invalide." in (
            main_text(soup)
        )
        assert soup.find("a", href=reverse("account_reset_password"))
        assert not soup.select("[role=main] form")

    def test_reset_link_works_only_once(self, client, mailoutbox):
        make_user()
        self.request_reset(client)
        path = link_in(mailoutbox[0])
        self.set_password(client, path)

        self.assert_token_fail(client.get(path, follow=True))

    def test_tampered_reset_link_fails(self, client, mailoutbox):
        make_user()
        self.request_reset(client)
        path = link_in(mailoutbox[0])
        tampered = path.rstrip("/")[:-3] + "xyz/"

        self.assert_token_fail(client.get(tampered, follow=True))

    def test_mismatched_passwords_keep_old_password(self, client, mailoutbox):
        user = make_user()
        self.request_reset(client)

        response = self.set_password(
            client, link_in(mailoutbox[0]), password2="Something-Else-2026!"
        )

        soup = intranet_page(response, "Modifier le mot de passe")
        assert "Vous devez saisir deux fois le même mot de passe." in main_text(soup)
        user.refresh_from_db()
        assert user.check_password(PASSWORD)

    def test_unknown_email_does_not_reveal_accounts(self, client, mailoutbox):
        self.assert_reset_requested(
            self.request_reset(client, email="nobody@example.com")
        )

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

        soup = intranet_page(client.get(path), "Confirmer l'adresse e-mail")

        assert (
            f"Merci de confirmer que {EMAIL} est l'adresse email de Jane Doe."
            in main_text(soup)
        )
        # The signed key embeds a timestamp, so the form may carry a fresher one
        form = soup.select_one("[role=main] form")
        assert form["action"].startswith("/accounts/confirm-email/")

        response = client.post(form["action"])

        assert response.url == "/"
        assert EmailAddress.objects.get(user=user, email=EMAIL).verified
        assert logged_in_user_pk(client) == user.pk

    def test_invalid_key_shows_expired_message(self, client):
        soup = intranet_page(
            client.get(reverse("account_confirm_email", args=["not-a-key"])),
            "Confirmer l'adresse e-mail",
        )

        assert "Ce lien de confirmation d'adresse email est expiré ou non valide." in (
            main_text(soup)
        )
        assert not soup.select("[role=main] form")


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

    def email_rows(self, client):
        soup = intranet_page(client.get(reverse("account_email")), "Adresses e-mail")
        return {
            squash(row.label.get_text()): squash(row.get_text())
            for row in soup.select("form.email_list .ctrlHolder")
        }

    def test_page_lists_addresses(self, client, user):
        soup = intranet_page(client.get(reverse("account_email")), "Adresses e-mail")

        assert {"action_primary", "action_send", "action_remove"} <= form_fields(
            soup, reverse("account_email")
        )
        assert self.email_rows(client) == {EMAIL: f"{EMAIL} Vérifiée Principale"}

    def test_add_email_sends_confirmation(self, client, user, mailoutbox):
        self.add_email(client)

        assert self.email_rows(client)[self.NEW_EMAIL] == (
            f"{self.NEW_EMAIL} Non vérifiée"
        )
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

        assert self.email_rows(client) == {
            EMAIL: f"{EMAIL} Vérifiée",
            self.NEW_EMAIL: f"{self.NEW_EMAIL} Vérifiée Principale",
        }
        user.refresh_from_db()
        assert user.email == self.NEW_EMAIL

    def test_unverified_email_cannot_become_primary(self, client, user):
        self.add_email(client)

        client.post(
            reverse("account_email"), {"action_primary": "", "email": self.NEW_EMAIL}
        )

        assert self.email_rows(client)[EMAIL] == f"{EMAIL} Vérifiée Principale"
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

    def test_resend_to_verified_email_sends_nothing(self, client, user, mailoutbox):
        response = client.post(
            reverse("account_email"), {"action_send": "", "email": EMAIL}, follow=True
        )

        assert mailoutbox == []
        soup = intranet_page(response, "Adresses e-mail")
        assert f"L'adresse e-mail {EMAIL} est déjà vérifiée." in main_text(soup)

    def test_resend_after_changing_primary(self, client, user, mailoutbox):
        self.add_email(client)
        client.post(link_in(mailoutbox[0]))
        client.post(
            reverse("account_email"), {"action_primary": "", "email": self.NEW_EMAIL}
        )
        cache.clear()
        sent_before = len(mailoutbox)

        soup = intranet_page(client.get(reverse("account_email")), "Adresses e-mail")
        checked = soup.select_one("form.email_list input[name=email][checked]")
        assert checked["value"] == self.NEW_EMAIL
        response = client.post(
            reverse("account_email"),
            {"action_send": "", "email": checked["value"]},
            follow=True,
        )

        assert len(mailoutbox) == sent_before
        soup = intranet_page(response, "Adresses e-mail")
        assert f"L'adresse e-mail {self.NEW_EMAIL} est déjà vérifiée." in main_text(
            soup
        )

    def test_resent_link_confirms_unverified_email(self, client, user, mailoutbox):
        self.add_email(client)
        cache.clear()
        client.post(
            reverse("account_email"), {"action_send": "", "email": self.NEW_EMAIL}
        )

        soup = intranet_page(
            client.get(link_in(mailoutbox[1])), "Confirmer l'adresse e-mail"
        )
        assert "expiré" not in main_text(soup)
        client.post(link_in(mailoutbox[1]))

        assert EmailAddress.objects.get(user=user, email=self.NEW_EMAIL).verified

    def test_anonymous_is_sent_to_login(self, client):
        response = client.get(reverse("account_email"))

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))

    def test_remove_secondary_email(self, client, user):
        self.add_email(client)

        client.post(
            reverse("account_email"), {"action_remove": "", "email": self.NEW_EMAIL}
        )

        assert list(self.email_rows(client)) == [EMAIL]


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

        soup = intranet_page(
            client.get(reverse("account_change_password")), "Modifier le mot de passe"
        )
        assert {"oldpassword", "password1", "password2"} <= form_fields(
            soup, reverse("account_change_password")
        )
        response = self.change(client)

        assert response.status_code == 302
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)
        assert logged_in_user_pk(client) == user.pk

    def test_wrong_old_password_is_refused(self, client):
        user = make_user()
        login(client)

        soup = intranet_page(
            self.change(client, oldpassword="wrong-password"),
            "Modifier le mot de passe",
        )

        assert "Merci d'indiquer votre mot de passe actuel." in main_text(soup)
        user.refresh_from_db()
        assert user.check_password(PASSWORD)


class TestProjectIntegration:
    def send_credentials(self, user, force=False):
        user.profile.send_credentials(
            {
                "fromuser": UserFactory(),
                "current_site": Site.objects.get_current(),
                "login_uri": "https://intranet.example.com/accounts/login/",
            },
            force=force,
        )

    @pytest.mark.parametrize("stored_email", [EMAIL, "Jane.Doe@Example.com"])
    def test_emailed_credentials_allow_login(self, client, mailoutbox, stored_email):
        user = UserFactory(email=stored_email, first_name="Jane", last_name="Doe")

        self.send_credentials(user)

        assert len(mailoutbox) == 1
        password = re.search(r"Mot de passe\s*: (\S+)", mailoutbox[0].body).group(1)
        response = login(client, password=password)
        assert response.url == "/"
        assert logged_in_user_pk(client) == user.pk

    def test_resent_credentials_make_the_new_email_the_only_primary(self, mailoutbox):
        user = make_user(email="old@example.com")
        user.email = EMAIL
        user.save()

        self.send_credentials(user, force=True)

        assert set(
            EmailAddress.objects.filter(user=user).values_list(
                "email", "verified", "primary"
            )
        ) == {("old@example.com", True, False), (EMAIL, True, True)}

    def test_failed_credentials_mail_changes_nothing(self):
        user = UserFactory(email=EMAIL, is_active=False)

        with patch.object(UserProfile, "send_mail", side_effect=SMTPException):
            with pytest.raises(SMTPException):
                self.send_credentials(user)

        user.refresh_from_db()
        assert not user.is_active
        assert not user.has_usable_password()
        assert not EmailAddress.objects.filter(user=user).exists()

    def test_createsuperuser_can_login(self, client):
        user = ProxyUser.objects.create_superuser("admin", EMAIL, PASSWORD)

        login(client)

        assert logged_in_user_pk(client) == user.pk
        assert EmailAddress.objects.get(user=user).verified
