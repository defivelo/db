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

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.article.models import Article
from defivelo.tests.utils import AuthClient, PowerUserAuthClient


class AuthUserTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = AuthClient()
        self.article = Article.objects.create(
            title="TestArticle",
            body="<h1>Test Body</h1>",
            published=True,
            modified=timezone.now(),
        )

    def test_my_restrictions(self):
        for symbolicurl in [
            "article-update",
            "article-delete",
        ]:
            response = self.client.get(
                reverse(symbolicurl, kwargs={"pk": self.article.pk})
            )
            self.assertEqual(response.status_code, 403, symbolicurl)

        response = self.client.get(reverse("article-create"))
        self.assertEqual(response.status_code, 403, "Article creation")


class PowerUserTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = PowerUserAuthClient()
        self.article = Article.objects.create(
            title="TestArticle",
            body="<h1>Test Body</h1>",
            published=True,
            modified=timezone.now(),
        )

    def test_my_accesses(self):
        for symbolicurl in [
            "article-update",
            "article-delete",
        ]:
            response = self.client.get(
                reverse(symbolicurl, kwargs={"pk": self.article.pk})
            )
            self.assertEqual(response.status_code, 200, symbolicurl)

        response = self.client.get(reverse("article-create"))
        self.assertEqual(response.status_code, 200, "Article creation request")

        response = self.client.post(
            reverse("article-create"),
            {"title": "New article", "body": "New body", "published": False},
        )
        self.assertEqual(response.status_code, 302, "Article creation")
