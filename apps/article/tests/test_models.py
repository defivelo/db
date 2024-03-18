# The MIT License (MIT)
#
# Copyright (c) 2015 Ha Pham
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from django.test import TestCase
from django.urls import reverse

from apps.article.models import Article
from defivelo.tests import utils


class ArticleModelTests(TestCase):
    def test_save(self):
        article = Article(title="Single One", summary="", body="Content")
        article.save()
        self.assertGreater(article.pk, 0)
        self.assertEqual(article.slug, "single-one")
        self.assertEqual(str(article), "Article: Single One")

    def test_duplicate(self):
        a0 = Article(title="Single One", summary="", body="Content")
        a0.save()
        a1 = Article(title="Single One", summary="", body="Content 2")
        a1.save()
        self.assertEqual(a1.slug, "single-one-1")

    def test_poweruser_only_can_crud_acrticles(self):
        article = Article(title="Single One", summary="", body="Content")
        article.save()

        # Any user
        self.client = utils.AuthClient()
        response = self.client.post(reverse("article-delete", args=[article.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Article.objects.count(), 1)

        # Power user
        self.client = utils.PowerUserAuthClient()
        response = self.client.post(reverse("article-delete", args=[article.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Article.objects.count(), 0)
