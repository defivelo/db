# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015 Didier Raboud <me+defivelo@odyx.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import activate

from allauth.account.models import EmailAddress

User = get_user_model()


class HomePageRedirectTest(TestCase):
    def setUp(self):
        self.userpassword = "top_secret"
        self.user = User.objects.create_user(
            username="jacob", email="jacob@example.com", password=self.userpassword
        )
        self.language = "fr"
        activate(self.language)

    def test_unauthenticated_homepage_redirects(self):
        # Issue a GET request.
        response = self.client.get("/")
        i18n_homepage = "/%s/" % self.language
        # Check that the response is 302 redirect to the language page
        self.assertRedirects(response, i18n_homepage, target_status_code=302)

        # Now fetch that language-based homepage
        response = self.client.get(i18n_homepage)

        # Check that the response is 302 redirect to the login page
        self.assertRedirects(
            response,
            "{login}?next={home}".format(
                login=reverse("account_login"), home=i18n_homepage
            ),
        )

    def test_login_with_username_fails(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": self.user.username, "password": self.userpassword,},
        )
        # The login failed, we're back on the same page
        self.assertTemplateUsed(response, "account/login.html")
        self.assertEqual(response.status_code, 200)

    def test_login_process_with_uncertified_email(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": self.user.email, "password": self.userpassword,},
        )
        # This triggered a mail sending to confirm that email
        self.assertEqual(EmailAddress.objects.count(), 1)
        self.assertFalse(EmailAddress.objects.first().verified)

        # Now confirm that email
        ec = EmailAddress.objects.get(user=self.user)
        ec.verified = True
        ec.set_as_primary(conditional=True)
        ec.save()
        # And retry login:
        response = self.client.post(
            reverse("account_login"),
            {"login": self.user.email, "password": self.userpassword,},
        )
        # This time, login worked
        self.assertTemplateUsed(response, "account/messages/logged_in.txt")
        self.assertEqual(response.status_code, 302)

    def test_signup_forbidden(self):
        response = self.client.get(reverse("account_signup"))

        # Check that the response is a 200 that uses the forbidden
        # signup template
        self.assertTemplateUsed(response, "account/signup_closed.html")
        self.assertEqual(response.status_code, 200)
