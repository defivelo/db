from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.challenge.tests.factories import QualificationFactory, SessionFactory

freeforallurls = ["public-nextqualifs", "public-json-nextqualifs"]


class AnonymousUserTest(TestCase):
    def setUp(self):
        self.session = SessionFactory(day=timezone.localdate())
        self.qualifs = QualificationFactory.create_batch(size=3, session=self.session)

    def test_access_to_qualifs_list(self):
        for symbolicurl in freeforallurls:
            url = reverse(symbolicurl)
            # Final URL is OK
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, url)
            self.assertIn(self.session.city.encode(), response.content)
