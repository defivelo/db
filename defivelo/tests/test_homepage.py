from django.core.urlresolvers import reverse
from django.test import TestCase


class HomePageRedirectTest(TestCase):
    def test_unauthenticated_homepage_redirects(self):
        # Issue a GET request.
        response = self.client.get('/')

        # Check that the response is 302 redirect to the login page
        self.assertRedirects(response, '%s?next=/' % reverse('login'))