# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from allauth.account.models import EmailAddress, EmailConfirmation
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone
from django.utils.translation import activate


class AuthClient(Client):
    USERNAME = 'foobar-authenticated'
    PASSWORD = 'sicrit'
    EMAIL = 'test@example.com'

    def __init__(self):
        super(AuthClient, self).__init__()
        # Create that user
        self.user = get_user_model().objects.create_user(
            username=self.USERNAME, password=self.PASSWORD,
            email=self.EMAIL
        )
        # Create his trusted Email
        EmailAddress.objects.create(user=self.user, email=self.EMAIL,
                                    verified=True, primary=True)
        self.login(email=self.EMAIL, password=self.PASSWORD)

        self.language = 'fr'
        activate(self.language)
