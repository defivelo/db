from allauth.account.models import EmailAddress, EmailConfirmation
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.translation import activate


class HomePageRedirectTest(TestCase):
    def setUp(self):
        self.userpassword = 'top_secret'
        self.user = User.objects.create_user(
            username='jacob',
            email='jacob@example.com',
            password=self.userpassword
        )
        self.language = 'fr'
        activate(self.language)

    def test_unauthenticated_homepage_redirects(self):
        # Issue a GET request.
        response = self.client.get('/')
        i18n_homepage = '/%s/' % self.language
        # Check that the response is 302 redirect to the language page
        self.assertRedirects(response, i18n_homepage,
                             target_status_code=302)

        # Now fetch that language-based homepage
        response = self.client.get(i18n_homepage)

        # Check that the response is 302 redirect to the login page
        self.assertRedirects(response,
                             '{login}?next={home}'.format(
                                 login=reverse('account_login'),
                                 home=i18n_homepage)
                             )

    def test_login_with_username_fails(self):
        response = self.client.post(
            reverse('account_login'),
            {
                'login': self.user.username,
                'password': self.userpassword,
            }
        )
        # The login failed, we're back on the same page
        self.assertTemplateUsed(response, 'account/login.html')
        self.assertEqual(response.status_code, 200)

    def test_login_process_with_uncertified_email(self):
        response = self.client.post(
            reverse('account_login'),
            {
                'login': self.user.email,
                'password': self.userpassword,
            }
        )
        # This triggered a mail sending to confirm that email
        self.assertEqual(EmailConfirmation.objects.count(), 1)
        # For one Email, of course
        self.assertEqual(EmailAddress.objects.count(), 1)

        # Now confirm that email
        ec = EmailAddress.objects.get(user=self.user)
        ec.verified = True
        ec.set_as_primary(conditional=True)
        ec.save()
        # And retry login:
        response = self.client.post(
            reverse('account_login'),
            {
                'login': self.user.email,
                'password': self.userpassword,
            }
        )
        # This time, login worked
        self.assertTemplateUsed(response, 'account/messages/logged_in.txt')
        self.assertEqual(response.status_code, 302)

    def test_signup_forbidden(self):
        response = self.client.get(reverse('account_signup'))

        # Check that the response is a 200 that uses the forbidden signup template
        self.assertTemplateUsed(response, 'account/signup_closed.html')
        self.assertEqual(response.status_code, 200)
