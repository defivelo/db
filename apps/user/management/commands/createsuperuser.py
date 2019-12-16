from django.contrib.auth.management.commands import createsuperuser
from django.contrib.auth.models import User, UserManager
from django.core.exceptions import ValidationError
from django.db import transaction

from allauth.account.models import EmailAddress

from apps.user.models import UserProfile


class ProxyUserManager(UserManager):
    @transaction.atomic
    def _create_user(self, username, email, password, **extra_fields):
        normalized_email = self.normalize_email(email)
        if self.filter(email=normalized_email).exists():
            raise ValidationError("User with this email already exists.")
        user = super()._create_user(username, email, password, **extra_fields)
        UserProfile.objects.create(user=user)
        return user

    @transaction.atomic
    def create_superuser(self, username, email, password, **extra_fields):
        user = super().create_superuser(username, email, password, **extra_fields)
        email_obj, _ = EmailAddress.objects.update_or_create(
            user=user, email=user.email, defaults=dict(verified=True)
        )
        email_obj.set_as_primary()
        return user


class ProxyUser(User):
    class Meta:
        proxy = True

    objects = ProxyUserManager()


class Command(createsuperuser.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.UserModel = ProxyUser
